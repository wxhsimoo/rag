from typing import Dict, Optional, Type

from ...infrastructure.log.logger_service import LoggerService
from .base import InfraDocumentSplitter
from .types import InfraSplitterConfig
from .markdown_splitter import MarkdownSplitter
from .json_splitter import JsonSplitter
from .text_splitter import TextSplitter
from .pdf_splitter import PdfSplitter
from .docx_splitter import DocxSplitter


class SplitterFactory:
    """文档切分器工厂类
    
    负责创建和管理各种类型的文档切分器
    """
    
    def __init__(self, logger: Optional[LoggerService] = None):
        """初始化工厂"""
        self.logger = logger
        self._splitters: Dict[str, Type[InfraDocumentSplitter]] = {}
        self._register_default_splitters()
    
    def _register_default_splitters(self) -> None:
        """注册默认的切分器"""
        try:
            # 注册JSON切分器
            self._splitters["json"] = JsonSplitter
            if self.logger:
                self.logger.info("Registered JsonSplitter")
            
            # 注册Markdown切分器
            self._splitters["markdown"] = MarkdownSplitter
            self._splitters["md"] = MarkdownSplitter
            if self.logger:
                self.logger.info("Registered MarkdownSplitter")

            # 注册Text切分器（txt/text）
            self._splitters["txt"] = TextSplitter
            self._splitters["text"] = TextSplitter
            if self.logger:
                self.logger.info("Registered TextSplitter for txt/text")

            # 注册PDF切分器
            self._splitters["pdf"] = PdfSplitter
            if self.logger:
                self.logger.info("Registered PdfSplitter")

            # 注册DOCX切分器
            self._splitters["docx"] = DocxSplitter
            if self.logger:
                self.logger.info("Registered DocxSplitter")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error registering default splitters: {str(e)}")
    
    def create_splitter(
        self,
        splitter_type: str,
        config: Optional[InfraSplitterConfig] = None
    ) -> Optional[InfraDocumentSplitter]:
        """创建指定类型的切分器
        
        Args:
            splitter_type: 切分器类型
            config: 切分器配置
            
        Returns:
            切分器实例，如果类型不支持则返回None
        """
        try:
            
            splitter_class = self._splitters.get(splitter_type)
            if splitter_class:
                # 创建切分器实例
                splitter = splitter_class(config, self.logger)
                
                if self.logger:
                    self.logger.debug(f"Created splitter: {splitter_type}")
                return splitter
            else:
                if self.logger:
                    self.logger.warning(f"Unsupported splitter type: {splitter_type}")
                return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating splitter {splitter_type}: {str(e)}")
            return None
