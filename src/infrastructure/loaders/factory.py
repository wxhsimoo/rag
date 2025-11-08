from typing import Dict, List, Optional, Type
from pathlib import Path

from .base import InfraDocumentLoader
from ...infrastructure.log.logger_service import LoggerService
from .json_loader import JsonDocumentLoader
from .markdown_loader import MarkdownDocumentLoader
from .pdf_loader import PdfDocumentLoader
from .text_loader import TextDocumentLoader
from .docx_loader import DocxDocumentLoader


class DocumentLoaderFactory:
    """文档加载器工厂
    
    负责创建和管理各种类型的文档加载器
    """
    
    def __init__(self, logger: Optional[LoggerService] = None):
        self.logger = logger
        self._loaders: Dict[str, InfraDocumentLoader] = {}
        
        # 注册默认加载器
        self._register_default_loaders()
    
    def _register_default_loaders(self):
        """注册默认的文档加载器"""
        # 注册JSON加载器
        json_loader = JsonDocumentLoader()
        self._loaders['json'] = json_loader

        # 注册Markdown加载器
        markdown_loader = MarkdownDocumentLoader()
        self._loaders['md'] = markdown_loader
        self._loaders['markdown'] = markdown_loader

        # 注册PDF加载器
        pdf_loader = PdfDocumentLoader(self.logger)
        self._loaders['pdf'] = pdf_loader

        # 注册Text加载器
        text_loader = TextDocumentLoader(self.logger)
        self._loaders['txt'] = text_loader
        self._loaders['text'] = text_loader

        # 注册DOCX加载器
        docx_loader = DocxDocumentLoader(self.logger)
        self._loaders['docx'] = docx_loader
        
        if self.logger:
            self.logger.info("已注册默认文档加载器")
    
    def get_loader(self, file_path: str, **kwargs) -> Optional[InfraDocumentLoader]:
        """获取适合指定文件的加载器
        
        Args:
            file_path: 文件路径
            **kwargs: 加载器初始化参数
            
        Returns:
            适合的加载器实例，如果没有找到则返回None
        """
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower().lstrip('.')
        
        # 检查加载器
        if extension in self._loaders:
            return self._loaders[extension]
        
        if self.logger:
            self.logger.warning(f"未找到适合文件类型 .{extension} 的加载器")
        return None
