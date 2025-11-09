import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from ...domain.interfaces.embedding_service import EmbeddingService
from ...domain.interfaces.llm_service import LLMService
from ...domain.interfaces.vector_store_service import VectorStoreService
from ...domain.entities.search_result import SearchResult
from ...domain.entities.user_query import UserQuery
from ...domain.interfaces.prompt_service import PromptService
from ...domain.entities.qa_context import QAContext, UserProfile, MessageRole
from ...infrastructure.log.logger_service import LoggerService

class RAGPipelineService:
    """RAG管道服务 - 通用文档问答系统"""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        vector_store_service: VectorStoreService,
        logger: LoggerService,
        prompt_service: PromptService,
    ):
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.vector_store_service = vector_store_service
        self.prompt_service = prompt_service
        self.logger = logger
        self.qa_context = QAContext()
    
    async def query(
        self,
        question: str,
        user_profile: Optional[UserProfile] = None,
        session_id: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """处理用户查询
        
        Args:
            question: 用户问题
            user_profile: 用户档案
            session_id: 会话ID
            top_k: 返回的相关文档数量
            
            
        Returns:
            查询结果
        """
        try:
            self.logger.info(f"处理查询: {question}")
            start_time = datetime.now()
            
            # 更新对话上下文
            if session_id :
                self.qa_context.add_message(
                    session_id=session_id,
                    role=MessageRole.USER,
                    content=question,
                    user_profile=user_profile
                )
            
            # 构建用户查询实体（用于分析与优化）
            user_query = UserQuery(
                question=question,
                normalized_question=self._enhance_query(question),
                session_id=session_id,
                user_id=(user_profile.user_id if user_profile else None),
                top_k=top_k,
                metadata={
                    "profile_present": user_profile is not None,
                },
            )

            # 1. 查询向量数据库获取相关文档
            relevant_docs = await self._retrieve_relevant_documents(
                question, top_k, user_profile
            )
            
            # 2. 构建提示词
            prompt = await self._build_prompt(
                question=question,
                relevant_docs=relevant_docs,
                user_profile=user_profile,
                session_id=session_id
            )
            
            # 3. 生成答案
            answer = await self.llm_service.generate_text(prompt)
            
            # 4. 后处理答案
            processed_answer = await self._post_process_answer(
                answer,
                relevant_docs=relevant_docs,
                question=question,
            )
            
            # 5. 更新对话上下文
            if session_id :
                self.qa_context.add_message(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=processed_answer["answer"]
                )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result = {
                "success": True,
                "answer": processed_answer["answer"],
                "structured_response": processed_answer.get("structured_response"),
                "sources": [{
                    "id": doc.document.doc_id,
                    "content": doc.document.content[:200] + "..." if len(doc.document.content) > 200 else doc.document.content,
                    "score": doc.score,
                    "metadata": doc.metadata
                } for doc in relevant_docs],
                "user_profile": user_profile.to_dict() if user_profile else None,
                "session_id": session_id,
                "user_query": user_query.to_dict(),
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            # 保存：用户原始问题 + 结果快照（会话维度，逻辑与 QAContext 一致）
            try:
                user_query.save(result)
            except Exception as save_err:
                self.logger.warning(f"UserQuery 保存失败: {save_err}")

            self.logger.info(f"查询处理完成，耗时 {processing_time:.2f} 秒")
            return result
            
        except Exception as e:
            self.logger.error(f"查询处理失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "answer": "抱歉，处理您的问题时出现了错误，请稍后再试。",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _retrieve_relevant_documents(
        self,
        question: str,
        top_k: int,
        user_profile: Optional[UserProfile] = None
    ) -> List[SearchResult]:
        """检索相关文档
        
        Args:
            question: 用户问题
            top_k: 返回的文档数量
            user_profile: 用户档案
            
        Returns:
            相关文档列表
        """
        try:
            # 通用查询
            enhanced_query = self._enhance_query(question)
            
            # 生成查询向量
            query_embedding = await self.embedding_service.embed_text(enhanced_query)
            
            # 搜索相关文档
            search_results = await self.vector_store_service.search_similar(
                query_embedding=query_embedding,
                top_k=top_k
            )
            return search_results
            
        except Exception as e:
            self.logger.error(f"检索相关文档失败: {str(e)}")
            raise
    
    def _enhance_query(self, question: str) -> str:
        """通用查询增强（当前直接返回原始问题）"""
        return question
    
    async def _build_prompt(
        self,
        question: str,
        relevant_docs: List[SearchResult],
        user_profile: Optional[UserProfile] = None,
        session_id: Optional[str] = None
    ) -> str:
        """构建提示词（委托给 PromptService）"""
        history_lines: Optional[List[str]] = None
        if session_id:
            history = self.qa_context.get_conversation_history(session_id, limit=3)
            if history:
                history_lines = []
                for msg in history[:-1]:  # 排除当前问题
                    role = "用户" if msg.role == MessageRole.USER else "助手"
                    history_lines.append(f"{role}: {msg.content}")

        return await self.prompt_service.build_prompt(
            question=question,
            relevant_docs=relevant_docs,
            user_profile=user_profile,
            history_lines=history_lines,
        )
    
    async def _post_process_answer(
        self,
        answer: str,
        relevant_docs: Optional[List[SearchResult]] = None,
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """后处理答案：优先解析固定 JSON 格式，失败则回退到启发式提取。
        
        固定格式期望：
        {
          "format": "structured_v1",
          "summary": string,
          "key_points": [string, ...],
          "citations": [{"source": string, "snippet": string}, ...]
        }
        """

        def _filter_point(text: str) -> bool:
            if not text:
                return False
            s = text.strip()
            sl = s.lower()
            if s.startswith(">"):
                return False
            if sl.startswith("来源") or sl.startswith("参考资料") or "参考资料" in s or sl.startswith("参考"):
                return False
            if sl.startswith("source"):
                return False
            if s.startswith("```") or s in {":", "："}:
                return False
            return True

        def _parse_json_block(text: str) -> Optional[Dict[str, Any]]:
            if not text:
                return None
            # 去除可能的代码块包裹
            cleaned = text.strip()
            if cleaned.startswith("```"):
                # 尝试移除三引号代码块
                cleaned = cleaned.strip("`")
                # 可能包含语言标识，如 ```json
                cleaned = cleaned.split("\n", 1)[-1].strip()
            # 提取 JSON 子串（第一个 { 到最后一个 }）
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            blob = cleaned[start:end+1]
            try:
                return json.loads(blob)
            except Exception:
                return None

        parsed = _parse_json_block(answer)

        if isinstance(parsed, dict) and parsed.get("format") == "structured_v1":
            summary = parsed.get("summary") or ""
            key_points = parsed.get("key_points") or []
            if isinstance(key_points, list):
                key_points = [kp.strip() for kp in key_points if isinstance(kp, str) and _filter_point(kp)][:6]
            else:
                key_points = []
            citations = parsed.get("citations") or []
            # 标准化 citations
            norm_citations: List[Dict[str, str]] = []
            if isinstance(citations, list):
                for c in citations:
                    if isinstance(c, dict):
                        src = c.get("source")
                        snip = c.get("snippet")
                        if isinstance(src, str) and isinstance(snip, str):
                            norm_citations.append({"source": src, "snippet": snip})

            plain_answer = summary.strip()
            if key_points:
                bullet_text = "\n".join(key_points)
                plain_answer = (plain_answer + "\n" + bullet_text).strip() if plain_answer else bullet_text

            structured_response = {
                "format": "structured_v1",
                "summary": summary,
                "key_points": key_points,
                "citations": norm_citations,
                "raw": answer,
                "question": question,
            }

            return {
                "answer": plain_answer or summary or "",
                "structured_response": structured_response,
            }

        # 回退：从自由文本中提取要点
        lines = [l.strip() for l in (answer.splitlines() if answer else [])]
        candidate_points = [l for l in lines if _filter_point(l)]
        bullet_points = [
            l for l in candidate_points
            if l.lstrip().startswith(('-', '*', '•', '·')) or any(l.lstrip().startswith(f"{i}.") for i in range(1, 10))
        ]
        key_points = (bullet_points if bullet_points else candidate_points)[:6]
        summary = lines[0] if lines else ""
        plain_answer = summary.strip()
        if key_points:
            bullet_text = "\n".join(key_points)
            plain_answer = (plain_answer + "\n" + bullet_text).strip() if plain_answer else bullet_text

        structured_response = {
            "format": "structured_v1",
            "summary": summary,
            "key_points": key_points,
            "citations": [],
            "raw": answer,
            "question": question,
        }

        return {
            "answer": plain_answer,
            "structured_response": structured_response,
        }
