from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from ...domain.interfaces import VectorStoreService
from ...domain.entities.search_result import SearchResult as DomainSearchResult
from ...domain.entities.document import Document as DomainDocument

@dataclass
class VectorDocument:
    """向量文档数据类"""
    id: str
    content: str
    metadata: Dict[str, Any] = None
    embedding: Optional[List[float]] = None

@dataclass
class SearchResult:
    """搜索结果数据类"""
    document: VectorDocument
    score: float
    distance: float

class VectorStore(VectorStoreService):
    """向量数据库接口"""
    
    @abstractmethod
    async def add_documents(self, documents: List[VectorDocument]) -> None:
        """添加文档到向量数据库
        
        Args:
            documents: 文档列表，包含内容和向量嵌入
        """
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], top_k: int = 5, **kwargs) -> List[SearchResult]:
        """向量相似度搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回最相似的k个结果
            **kwargs: 其他搜索参数
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def update_document(self, document: VectorDocument) -> bool:
        """更新文档
        
        Args:
            document: 更新的文档
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """获取文档总数
        
        Returns:
            文档总数
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空所有文档"""
        pass
    
    # Domain层接口实现
    def _vector_to_domain_document(self, vector_doc: VectorDocument) -> DomainDocument:
        """将VectorDocument转换为Domain层Document"""
        return DomainDocument(
            content=vector_doc.content,
            metadata=vector_doc.metadata or {},
            doc_id=vector_doc.id
        )
    
    def _domain_to_vector_document(self, domain_doc: DomainDocument, embedding: List[float]) -> VectorDocument:
        """将Domain层Document转换为VectorDocument"""
        return VectorDocument(
            id=domain_doc.doc_id,
            content=domain_doc.content,
            metadata=domain_doc.metadata,
            embedding=embedding
        )
    
    def _search_result_to_domain(self, result: SearchResult) -> DomainSearchResult:
        """将SearchResult转换为Domain层SearchResult"""
        return DomainSearchResult(
            document=self._vector_to_domain_document(result.document),
            score=result.score,
            metadata={"distance": result.distance}
        )
    
    async def add_documents_with_vectors(self, documents: List[DomainDocument], 
                                       vectors: List[List[float]]) -> None:
        """添加文档和向量 - Domain层接口"""
        vector_docs = []
        for doc, vector in zip(documents, vectors):
            vector_docs.append(self._domain_to_vector_document(doc, vector))
        await self.add_documents(vector_docs)
    
    async def search_similar(self, query_embedding: List[float], top_k: int = 5, 
                           filters: Optional[Dict[str, Any]] = None) -> List[DomainSearchResult]:
        """相似度搜索 - Domain层接口"""
        results = await self.search(query_embedding, top_k, **(filters or {}))
        return [self._search_result_to_domain(result) for result in results]
    
    async def delete_documents(self, document_ids: List[str]) -> int:
        """批量删除文档 - Domain层接口"""
        deleted_count = 0
        for doc_id in document_ids:
            if await self.delete_document(doc_id):
                deleted_count += 1
        return deleted_count
    
    async def update_document_with_vector(self, document: DomainDocument, 
                                        vector: List[float]) -> bool:
        """更新文档和向量 - Domain层接口"""
        vector_doc = self._domain_to_vector_document(document, vector)
        return await self.update_document(vector_doc)
    
    async def get_document_by_id(self, document_id: str) -> Optional[DomainDocument]:
        """根据ID获取文档 - Domain层接口"""
        vector_doc = await self.get_document(document_id)
        return self._vector_to_domain_document(vector_doc) if vector_doc else None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息 - Domain层接口"""
        return {
            "total_documents": await self.count(),
            "index_size": await self.count()  # 简化实现
        }
    
    @abstractmethod
    async def is_available(self) -> bool:
        """检查服务可用性 - Domain层接口"""
        pass
    
    async def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息 - Domain层接口"""
        return {
            "type": "vector_store",
            "total_documents": await self.count(),
            "available": await self.is_available()
        }
