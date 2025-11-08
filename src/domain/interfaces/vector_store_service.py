from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from ..entities.document import Document
from ..entities.search_result import SearchResult


class VectorStoreService(ABC):
    """向量存储服务接口 - 定义向量存储和检索的抽象方法"""
    
    @abstractmethod
    async def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> bool:
        """添加文档和对应的向量
        
        Args:
            documents: 文档列表
            embeddings: 对应的向量列表
            
        Returns:
            添加是否成功
        """
        pass
    
    @abstractmethod
    async def add_documents_with_vectors(self, documents: List[Document], embeddings: List[List[float]]) -> bool:
        """添加文档和对应的向量（别名方法）
        
        Args:
            documents: 文档列表
            embeddings: 对应的向量列表
            
        Returns:
            添加是否成功
        """
        pass
    
    @abstractmethod
    async def add_document(self, document: Document, embedding: List[float]) -> bool:
        """添加单个文档和向量
        
        Args:
            document: 文档
            embedding: 对应的向量
            
        Returns:
            添加是否成功
        """
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], top_k: int = 10, 
                    filter_criteria: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """向量搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_criteria: 过滤条件
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    async def search_similar(self, query_embedding: List[float], top_k: int = 5,
                               filter_criteria: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """相似度搜索（返回前 top_k 条）
        
        Args:
            query_embedding: 查询向量
            top_k: 返回的结果条数
            filter_criteria: 过滤条件
            
        Returns:
            相似度最高的前 top_k 条结果
        """
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """根据ID获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """删除文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            删除是否成功
        """
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> int:
        """批量删除文档
        
        Args:
            document_ids: 文档ID列表
            
        Returns:
            成功删除的文档数量
        """
        pass
    
    @abstractmethod
    async def update_document(self, document: Document, embedding: List[float]) -> bool:
        """更新文档和向量
        
        Args:
            document: 更新后的文档
            embedding: 更新后的向量
            
        Returns:
            更新是否成功
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
    async def clear(self) -> bool:
        """清空所有文档
        
        Returns:
            清空是否成功
        """
        pass
    
    @abstractmethod
    async def save_index(self, path: Optional[str] = None) -> bool:
        """保存索引
        
        Args:
            path: 保存路径，如果为None则使用默认路径
            
        Returns:
            保存是否成功
        """
        pass
    
    @abstractmethod
    async def load_index(self, path: Optional[str] = None) -> bool:
        """加载索引
        
        Args:
            path: 加载路径，如果为None则使用默认路径
            
        Returns:
            加载是否成功
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """获取向量维度
        
        Returns:
            向量维度
        """
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """检查服务是否可用
        
        Returns:
            服务是否可用
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息
        
        Returns:
            服务信息字典
        """
        pass
