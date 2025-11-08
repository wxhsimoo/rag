from abc import ABC, abstractmethod
from typing import List, Optional, Any

from ...infrastructure.prompt.types import PromptContext, PromptDoc
from ..entities.search_result import SearchResult
from ..entities.qa_context import UserProfile


class PromptService(ABC):
    """提示词构建服务接口（基于基础设施层 PromptContext）
    
    接口统一接收 PromptContext，避免直接暴露领域类型到构建器实现。
    """

    @abstractmethod
    async def build_prompt(self, ctx: PromptContext) -> str:
        """构建模型提示词
        
        Args:
            ctx: 基础设施层的提示上下文对象
        Returns:
            prompt 字符串
        """
        raise NotImplementedError


class PromptServiceAdapter:
    """适配器：提供旧入参签名，内部转换为 PromptContext 后委托 PromptService。
    
    旧签名：question、relevant_docs(List[SearchResult])、user_profile、history_lines
    新调用：构造 PromptContext 并调用 impl.build_prompt(ctx)
    """

    def __init__(self, impl: PromptService):
        self._impl = impl

    async def build_prompt(
        self,
        question: str,
        relevant_docs: List[SearchResult],
        user_profile: Optional[UserProfile] = None,
        history_lines: Optional[List[str]] = None,
    ) -> str:
        docs: List[PromptDoc] = []
        for doc in relevant_docs:
            source = None
            if doc.metadata:
                source = doc.metadata.get("source") or doc.metadata.get("document_id")
            content = doc.document.content if hasattr(doc.document, "content") else str(doc.document)
            docs.append(PromptDoc(content=content, source=source))

        ctx = PromptContext(
            question=question,
            docs=docs,
            history_lines=history_lines or [],
            user_profile=user_profile.dict() if hasattr(user_profile, "dict") else (user_profile or None),
        )

        return await self._impl.build_prompt(ctx)
