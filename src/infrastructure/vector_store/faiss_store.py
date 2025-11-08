import os
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS as LangChainFAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document as LangChainDocument

from .base import VectorStore, VectorDocument, SearchResult
from ...infrastructure.config.config_manager import get_config


class FAISSVectorStore(VectorStore):
    """基于LangChain的FAISS向量数据库实现"""

    def __init__(self, dimension: int = None, index_path: str = None, embedding_service=None):
        # 使用配置中的缺省值，确保在未传参时也可正常工作
        cfg = get_config()
        self.dimension = int(dimension) if dimension is not None else int(cfg.storage.vector_store.dimension)
        self.index_path = os.path.normpath(index_path) if index_path is not None else os.path.normpath(cfg.storage.vector_store.index_path)
        self.embedding_service = embedding_service
        # 延后到 _initialize_langchain_faiss 中按需构造
        self.langchain_faiss = None
        # 创建索引目录
        os.makedirs(self.index_path, exist_ok=True)
        
        # 初始化LangChain FAISS向量存储
        self._initialize_langchain_faiss()
        
        # 文档映射（用于兼容性）
        self.documents: Dict[str, VectorDocument] = {}
        
        # 尝试加载已存在的索引
        self._load_index()

    def _initialize_langchain_faiss(self):
        """初始化LangChain FAISS向量存储"""
        import faiss
        if not self.embedding_service:
            # 如果没有提供嵌入提供者，创建一个空的FAISS索引
            index = faiss.IndexFlatL2(self.dimension)
            self.langchain_faiss = LangChainFAISS(
                embedding_function=None,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={}
            )
        else:
            # 使用提供的嵌入提供者创建FAISS索引
            index = faiss.IndexFlatL2(self.dimension)
            self.langchain_faiss = LangChainFAISS(
                embedding_function=self.embedding_service,
                index=index,
                docstore=InMemoryDocstore(),
                index_to_docstore_id={}
            )

    def _get_expected_index_files(self) -> List[str]:
        """返回期望存在的索引文件列表（由 LangChain 保存）"""
        return [
            os.path.normpath(os.path.join(self.index_path, "index.faiss")),
            os.path.normpath(os.path.join(self.index_path, "index.pkl")),
        ]

    def _has_existing_index(self) -> bool:
        """检测索引目录中是否存在已保存的索引文件"""
        for path in self._get_expected_index_files():
            if os.path.exists(path):
                return True
        return False

    def _vector_document_to_langchain_document(self, vector_doc: VectorDocument) -> LangChainDocument:
        """将VectorDocument转换为LangChain Document"""
        return LangChainDocument(
            page_content=vector_doc.content,
            metadata=vector_doc.metadata or {}
        )

    def _langchain_document_to_vector_document(self, doc: LangChainDocument, doc_id: str, embedding: List[float] = None) -> VectorDocument:
        """将LangChain Document转换为VectorDocument"""
        return VectorDocument(
            id=doc_id,
            content=doc.page_content,
            metadata=doc.metadata,
            embedding=embedding
        )

    def _load_index(self):
        """加载已存在的索引"""
        try:
            expected_files = self._get_expected_index_files()
            existing_files = [p for p in expected_files if os.path.exists(p)]
            if existing_files:
                # 使用LangChain的加载功能；如无嵌入服务，则使用占位嵌入以满足接口
                embeddings = self.embedding_service or self._create_dummy_embeddings()
                self.langchain_faiss = LangChainFAISS.load_local(
                    self.index_path,
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
                # 尝试同步维度为索引真实维度
                if hasattr(self.langchain_faiss, 'index'):
                    try:
                        self.dimension = int(getattr(self.langchain_faiss.index, 'd', self.dimension))
                    except Exception:
                        pass
                # 将 docstore 中的文档同步到本地映射，并补齐元数据中的 id
                try:
                    ds = getattr(self.langchain_faiss, 'docstore', None)
                    if ds is not None:
                        # InMemoryDocstore 将文档保存在 _dict
                        raw = getattr(ds, '_dict', {}) or {}
                        for doc_id, doc in raw.items():
                            md = dict(getattr(doc, 'metadata', {}) or {})
                            # 确保检索结果里可以拿到原始 doc_id
                            md.setdefault('id', doc_id)
                            # 保存到本地兼容映射（不包含向量）
                            self.documents[doc_id] = VectorDocument(
                                id=doc_id,
                                content=getattr(doc, 'page_content', '') or '',
                                metadata=md,
                                embedding=None,
                            )
                except Exception:
                    # 同步失败不阻塞索引加载
                    pass
                print(f"成功加载FAISS索引文件: {', '.join(existing_files)}")
            else:
                # 未发现索引文件，保持空索引可用
                print("索引目录未发现 index.faiss/index.pkl，将创建新索引")
                # 重新初始化以确保干净状态
                self._initialize_langchain_faiss()

        except Exception as e:
            print(f"加载索引失败，将创建新索引: {str(e)}")
            self._initialize_langchain_faiss()

    def _save_index(self):
        """保存索引到文件"""
        try:
            if self.langchain_faiss and hasattr(self.langchain_faiss, 'save_local'):
                # 使用LangChain的保存功能
                self.langchain_faiss.save_local(self.index_path)
                print(f"成功保存LangChain FAISS索引到: {self.index_path}")
            else:
                print("LangChain FAISS实例不可用，跳过保存")
        except Exception as e:
            raise Exception(f"保存索引失败: {str(e)}")

    async def add_documents(self, documents: List[VectorDocument]) -> None:
        """添加文档到向量数据库"""
        try:
            if not documents:
                return
                
            # 转换为LangChain文档格式
            langchain_docs = []
            doc_ids = []
            
            for doc in documents:
                langchain_doc = self._vector_document_to_langchain_document(doc)
                langchain_docs.append(langchain_doc)
                doc_ids.append(doc.id)
                
                # 保存到本地映射（用于兼容性）
                self.documents[doc.id] = doc
            
            # 如果有嵌入向量，直接添加
            if documents[0].embedding is not None:
                embeddings = [doc.embedding for doc in documents]
                text_embedding_pairs = list(zip([doc.content for doc in documents], embeddings))
                
                # 使用from_embeddings创建或合并到现有索引
                if hasattr(self.langchain_faiss, 'index') and self.langchain_faiss.index.ntotal == 0:
                    # 如果是空索引，重新创建
                    self.langchain_faiss = LangChainFAISS.from_embeddings(
                        text_embedding_pairs,
                        self.embedding_service or self._create_dummy_embeddings(),
                        ids=doc_ids
                    )
                else:
                    # 添加到现有索引
                    self.langchain_faiss.add_embeddings(text_embedding_pairs, ids=doc_ids)
            else:
                # 使用嵌入提供者生成嵌入
                if self.embedding_service:
                    self.langchain_faiss.add_documents(langchain_docs, ids=doc_ids)
                else:
                    raise ValueError("缺少嵌入向量且未提供嵌入提供者")
            
            # 保存索引
            self._save_index()
            
        except Exception as e:
            print(f"FAISS存储错误详情: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"添加文档失败: {str(e)}")
    
    def _create_dummy_embeddings(self):
        """创建虚拟嵌入提供者（用于直接提供嵌入向量的情况）"""
        dim = int(self.dimension)
        class DummyEmbeddings:
            def embed_documents(self, texts):
                return [[0.0] * dim for _ in texts]
            def embed_query(self, text):
                return [0.0] * dim
        return DummyEmbeddings()

    async def search(
        self, query_embedding: List[float], top_k: int = 5, **kwargs
    ) -> List[SearchResult]:
        """向量相似度搜索"""
        try:
            # 防御性处理，避免传入 numpy.int64 等导致下游库报错
            try:
                top_k = int(top_k)
            except Exception:
                top_k = 5
            if not self.langchain_faiss or (hasattr(self.langchain_faiss, 'index') and self.langchain_faiss.index.ntotal == 0):
                return []
            
            # 使用LangChain FAISS的similarity_search_by_vector功能
            langchain_docs_with_scores = self.langchain_faiss.similarity_search_with_score_by_vector(
                query_embedding, k=top_k
            )
            
            results = []
            for langchain_doc, score in langchain_docs_with_scores:
                # 从metadata中获取文档ID
                doc_id = langchain_doc.metadata.get('id')
                if doc_id and doc_id in self.documents:
                    document = self.documents[doc_id]
                    results.append(
                        SearchResult(
                            document=document,
                            score=float(score),
                            distance=1.0 - float(score),  # 相似度转距离
                        )
                    )
                else:
                    # 如果本地映射中没有，从LangChain文档创建
                    vector_doc = self._langchain_document_to_vector_document(
                        langchain_doc, 
                        doc_id or f"doc_{len(results)}"
                    )
                    results.append(
                        SearchResult(
                            document=vector_doc,
                            score=float(score),
                            distance=1.0 - float(score),
                        )
                    )
            
            return results
            
        except Exception as e:
            raise Exception(f"搜索失败: {str(e)}")

    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            if document_id not in self.documents:
                return False

            # 从本地映射中删除
            del self.documents[document_id]
            
            # 使用LangChain FAISS的delete功能
            if hasattr(self.langchain_faiss, 'delete') and hasattr(self.langchain_faiss, 'docstore'):
                try:
                    # 尝试删除文档
                    self.langchain_faiss.delete([document_id])
                except Exception as e:
                    print(f"LangChain FAISS删除失败，将重建索引: {e}")
                    # 如果删除失败，重建索引
                    await self._rebuild_index()
            else:
                # 如果不支持删除，重建索引
                await self._rebuild_index()
            
            # 保存索引
            self._save_index()
            return True

        except Exception as e:
            raise Exception(f"删除文档失败: {str(e)}")

    async def update_document(self, document: VectorDocument) -> bool:
        """更新文档"""
        try:
            if document.id not in self.documents:
                return False

            # 删除旧文档并添加新文档
            await self.delete_document(document.id)
            await self.add_documents([document])

            return True

        except Exception as e:
            raise Exception(f"更新文档失败: {str(e)}")

    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        return self.documents.get(document_id)

    async def count(self) -> int:
        """获取文档数量"""
        if self.langchain_faiss and hasattr(self.langchain_faiss, 'index'):
            return self.langchain_faiss.index.ntotal
        return len(self.documents)

    async def clear(self) -> bool:
        """清空所有文档"""
        try:
            # 清空本地映射
            self.documents = {}
            
            # 重新初始化LangChain FAISS
            self._initialize_langchain_faiss()
            
            # 保存空索引
            self._save_index()
            return True
        except Exception as e:
            raise Exception(f"清空索引失败: {str(e)}")

    async def _rebuild_index(self):
        """重建索引"""
        try:
            # 保存当前文档
            current_docs = list(self.documents.values())

            # 重新初始化LangChain FAISS
            self._initialize_langchain_faiss()

            # 清空本地映射
            self.documents = {}

            # 重新添加文档
            if current_docs:
                await self.add_documents(current_docs)

        except Exception as e:
            raise Exception(f"重建索引失败: {str(e)}")

    def _vector_document_to_domain_document(self, vector_doc: VectorDocument):
        """将VectorDocument转换为Domain层Document实体"""
        from ...domain.entities.document import Document

        return Document(
            content=vector_doc.content,
            metadata=vector_doc.metadata,
            doc_id=vector_doc.id,
            doc_type=vector_doc.metadata.get("doc_type", "unknown"),
            source_path=vector_doc.metadata.get("source_path", ""),
        )

    def _domain_document_to_vector_document(self, domain_doc, embedding: List[float]):
        """将Domain层Document实体转换为VectorDocument"""
        return VectorDocument(
            id=domain_doc.doc_id,
            content=domain_doc.content,
            embedding=embedding,
            metadata=domain_doc.metadata,
        )

    async def delete_documents(self, document_ids: List[str]) -> int:
        """批量删除文档"""
        deleted_count = 0
        for doc_id in document_ids:
            if await self.delete_document(doc_id):
                deleted_count += 1
        return deleted_count

    async def update_document_with_vector(
        self, document, embedding: List[float]
    ) -> bool:
        """更新带向量的文档"""
        from ...domain.entities.document import Document

        if isinstance(document, Document):
            vector_doc = self._domain_document_to_vector_document(document, embedding)
            return await self.update_document(vector_doc)
        return await self.update_document(document)

    async def get_document_by_id(self, document_id: str):
        """根据ID获取文档"""
        vector_doc = await self.get_document(document_id)
        if vector_doc:
            return self._vector_document_to_domain_document(vector_doc)
        return None

    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        # 反映实际索引类型
        idx_type = "unknown"
        try:
            if self.langchain_faiss and hasattr(self.langchain_faiss, 'index') and self.langchain_faiss.index is not None:
                idx_type = type(self.langchain_faiss.index).__name__
        except Exception:
            pass
        return {
            "total_documents": await self.count(),
            "index_dimension": self.dimension,
            "index_type": f"FAISS_{idx_type}",
            "storage_path": self.index_path,
        }

    async def is_available(self) -> bool:
        """检查服务可用性"""
        try:
            # 检查索引是否正常
            return bool(self.langchain_faiss and hasattr(self.langchain_faiss, 'index') and self.langchain_faiss.index is not None)
        except Exception:
            return False

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "provider": "faiss",
            "dimension": self.dimension,
            "index_path": self.index_path,
            "total_documents": len(self.documents),
            "index_type": "IndexFlatIP",
        }

    # Domain层接口实现
    async def add_document(self, document, embedding: List[float]) -> bool:
        """添加单个文档和向量 - Domain层接口"""
        try:
            vector_doc = self._domain_document_to_vector_document(document, embedding)
            await self.add_documents([vector_doc])
            return True
        except Exception:
            return False

    async def add_documents_with_vectors(
        self, documents: List, embeddings: List[List[float]]
    ) -> bool:
        """添加文档和向量 - Domain层接口"""
        try:
            vector_docs = []
            for doc, embedding in zip(documents, embeddings):
                vector_doc = self._domain_document_to_vector_document(doc, embedding)
                vector_docs.append(vector_doc)
            await self.add_documents(vector_docs)
            return True
        except Exception as e:
            print(f"存储向量失败: {str(e)}")
            return False

    async def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ):
        """相似度搜索（委托基类进行领域类型转换）"""
        return await super().search_similar(query_embedding, top_k, filters)

    async def update_document_with_vector(self, document, vector: List[float]) -> bool:
        """更新文档和向量 - Domain层接口"""
        vector_doc = self._domain_document_to_vector_document(document, vector)
        return await self.update_document(vector_doc)

    async def get_document_by_id(self, document_id: str):
        """根据ID获取文档 - Domain层接口"""
        vector_doc = await self.get_document(document_id)
        return (
            self._vector_document_to_domain_document(vector_doc) if vector_doc else None
        )

    async def similarity_search(
        self,
        query_embedding: List[float],
        threshold: float = 0.7,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List:
        """相似度搜索 - Domain层接口"""
        # 先进行常规搜索，然后过滤阈值
        results = await self.search(query_embedding, top_k=100)  # 获取更多结果用于过滤
        filtered_results = []

        for result in results:
            if result.score >= threshold:
                domain_result = {
                    "document": self._vector_document_to_domain_document(
                        result.document
                    ),
                    "score": result.score,
                    "distance": result.distance,
                }
                filtered_results.append(domain_result)

        return filtered_results

    async def save_index(self, path: Optional[str] = None) -> bool:
        """保存索引 - Domain层接口"""
        try:
            if path:
                # 临时更改路径
                original_path = self.index_path
                self.index_path = path
                self._save_index()
                self.index_path = original_path
            else:
                self._save_index()
            return True
        except Exception:
            return False

    async def load_index(self, path: Optional[str] = None) -> bool:
        """加载索引 - Domain层接口"""
        try:
            if path:
                # 临时更改路径
                original_path = self.index_path
                self.index_path = path
                self._load_index()
                self.index_path = original_path
            else:
                self._load_index()
            return True
        except Exception:
            return False

    def get_dimension(self) -> int:
        """获取向量维度 - Domain层接口"""
        return self.dimension
