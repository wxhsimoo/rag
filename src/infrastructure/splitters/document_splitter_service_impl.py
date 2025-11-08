from typing import List, Optional

from ...infrastructure.log.logger_service import LoggerService
from .factory import SplitterFactory
from .types import InfraSplitterConfig, InfraDocument, InfraDocumentChunk


class DocumentSplitterServiceImpl:
    """文档切分服务实现"""
    
    def __init__(self, long_document_threshold: int = 10, logger: Optional[LoggerService] = None):
        self.splitter_factory = SplitterFactory(logger)
        self.long_document_threshold = long_document_threshold
        self.logger = logger
    
    async def should_split_document(self, document: InfraDocument) -> bool:
        """判断文档是否需要切分
        
        Args:
            document: 文档
            
        Returns:
            是否需要切分
        """
        try:
            content_length = len(document.content)
            
            # 基于长度判断
            if content_length > self.long_document_threshold:
                return True
            
            # 基于内容结构判断
            if self.has_complex_structure(document):
                return True
            
            return False
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"判断文档是否需要切分失败: {str(e)}")
            return False
    
    async def split_document(
        self,
        document: InfraDocument,
    ) -> List[InfraDocumentChunk]:
        """切分单个文档
        
        Args:
            document: 要切分的文档
            splitter_type: 切分器类型
            config: 切分器配置
            
        Returns:
            文档块列表
        """
        try:
            # TODO 改为从配置文件读取
            config = InfraSplitterConfig(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", "。", "！", "？", ";", ":", " ", ""]
            )
            
            # 创建切分器并进行切分
            document.doc_type = document.doc_type[1:]
            infra_splitter = self.splitter_factory.create_splitter(document.doc_type, config)
            # 使用切分器自身的配置进行切分，不再传入第二个位置参数
            chunks = infra_splitter.split_document(document)
            
            if self.logger:
                self.logger.info(f"文档 {document.doc_id} 切分完成，生成 {len(chunks)} 个块")
            return chunks
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"文档切分失败 {document.doc_id}: {str(e)}")
            return []
    
    def has_complex_structure(self, document: InfraDocument) -> bool:
        """检查文档是否有复杂结构
        
        Args:
            document: 文档
            
        Returns:
            是否有复杂结构
        """
        content = document.content
        
        # 检查段落数量
        paragraphs = content.split("\n\n")
        if len(paragraphs) > 5:
            return True
        
        # 检查列表项
        lines = content.split("\n")
        list_items = [line for line in lines if line.strip().startswith(("1.", "2.", "3.", "•", "-", "*"))]
        if len(list_items) > 3:
            return True
        
        return False
