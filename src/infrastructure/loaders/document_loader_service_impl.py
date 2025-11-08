from typing import List, Optional
from pathlib import Path

from ..splitters.types import InfraDocument
from ...infrastructure.log.logger_service import LoggerService
from .factory import DocumentLoaderFactory


class DocumentLoaderServiceImpl:
    """文档加载服务实现
    
    根据文件后缀调用不同的infrastructure/loaders具体实现类
    """
    
    def __init__(self, logger: Optional[LoggerService] = None):
        self.logger = logger
        self.loader_factory = DocumentLoaderFactory(logger)
    
    def load_document(self, file_path: str) -> List[InfraDocument]:
        """加载单个文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档列表（一个文件可能产生多个文档块）
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持或内容无效
        """
        # 验证文件存在
        if not Path(file_path).exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取适合的加载器
        loader = self.loader_factory.get_loader(file_path)
        if not loader:
            extension = Path(file_path).suffix.lower().lstrip('.')
            raise ValueError(f"不支持的文件类型: .{extension}")
        
        if self.logger:
            self.logger.info(f"使用 {loader.__class__.__name__} 加载文档: {file_path}")
        
        # 加载文档
        documents = loader.load(file_path)
        
        if self.logger:
            self.logger.info(f"从 {file_path} 加载了 {len(documents)} 个文档")
        
        return documents
