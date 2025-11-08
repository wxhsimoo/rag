from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from ..entities.document import Document

class DocumentStorageService(ABC):
    """文档存储管理服务接口 - 定义文档存储和检索的抽象方法"""
    
    @abstractmethod
    async def load_documents(self, source_path: Optional[str] = None) -> List[Document]:
        """加载文档
        
        Args:
            source_path: 文档源路径或前缀
                - 本地实现：作为根目录/子目录过滤
                - S3实现：作为对象键前缀（prefix）
            
        Returns:
            文档列表
        """

        
        pass
    
    @abstractmethod
    async def save_document(self, document: Document) -> Tuple[bool, str]:
        """保存文档
        
        Args:
            document: 要保存的文档
            
        Returns:
            (保存是否成功, 文档ID)
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
    async def list_documents(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出文档
        
        Args:
            category: 文档分类或标签/前缀，用于过滤（实现可选支持）
            
        Returns:
            文档信息列表（至少包含 id/source/metadata）
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
    async def search_documents(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Document]:
        """搜索文档
        
        Args:
            query: 搜索查询
            category: 文档分类
            limit: 返回结果数量限制
            
        Returns:
            匹配的文档列表
        """
        pass
    
    @abstractmethod
    async def get_document_count(self, category: Optional[str] = None) -> int:
        """获取文档数量
        
        Args:
            category: 文档分类，如果为None则返回总数量
            
        Returns:
            文档数量
        """
        pass
    
    @abstractmethod
    async def update_document(self, document: Document) -> bool:
        """更新文档
        
        Args:
            document: 要更新的文档
            
        Returns:
            更新是否成功
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的文档格式
        
        Returns:
            支持的文档格式列表
        """
        pass
    
    @abstractmethod
    async def validate_document(self, document: Document) -> bool:
        """验证文档
        
        Args:
            document: 要验证的文档
            
        Returns:
            验证是否通过
        """
        pass
