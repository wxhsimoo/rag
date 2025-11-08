from abc import ABC, abstractmethod
from typing import List

from ..entities.document import Document


class DocumentLoaderService(ABC):
    """文档加载服务接口
    
    定义文档加载服务的标准接口，负责根据文件路径数组加载文档
    """
    
    @abstractmethod
    def load_document(self, file_path: str) -> List[Document]:
        """加载单个文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档列表（一个文件可能产生多个文档块）
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持或内容无效
        """
        pass


class DocumentLoader(ABC):
    """文档加载器接口
    
    定义文档加载器的标准接口，所有具体的加载器都应该实现这个接口
    """
    
    @abstractmethod
    def load(self, file_path: str) -> List[Document]:
        """加载文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持或内容无效
        """
        pass
