"""文档切分服务接口和实现

定义文档切分的核心业务逻辑接口和基础实现
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..entities.document import Document
from ..entities.document_chunk import DocumentChunk
from ...infrastructure.log.logger_service import LoggerService


class SplitterType(Enum):
    """切分器类型枚举"""
    RECURSIVE_CHARACTER = "recursive_character"
    CHARACTER = "character"
    TOKEN = "token"
    SEMANTIC = "semantic"
    MARKDOWN = "markdown"
    MD = "md"
    JSON = "json"
    CODE = "code"
    CUSTOM = "custom"


@dataclass
class SplitterConfig:
    """切分器配置"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: Optional[List[str]] = None
    keep_separator: bool = True
    add_start_index: bool = True
    strip_whitespace: bool = True
    
    # 语义切分相关配置
    similarity_threshold: float = 0.5
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    
    # 其他配置
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'separators': self.separators,
            'keep_separator': self.keep_separator,
            'add_start_index': self.add_start_index,
            'strip_whitespace': self.strip_whitespace,
            'similarity_threshold': self.similarity_threshold,
            'min_chunk_size': self.min_chunk_size,
            'max_chunk_size': self.max_chunk_size,
            'custom_params': self.custom_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SplitterConfig':
        """从字典创建配置"""
        return cls(
            chunk_size=data.get('chunk_size', 1000),
            chunk_overlap=data.get('chunk_overlap', 200),
            separators=data.get('separators'),
            keep_separator=data.get('keep_separator', True),
            add_start_index=data.get('add_start_index', True),
            strip_whitespace=data.get('strip_whitespace', True),
            similarity_threshold=data.get('similarity_threshold', 0.5),
            min_chunk_size=data.get('min_chunk_size', 100),
            max_chunk_size=data.get('max_chunk_size', 2000),
            custom_params=data.get('custom_params', {})
        )


class DocumentSplitter(ABC):
    """文档切分器抽象基类
    
    定义文档切分器的基本接口和行为
    """
    
    def __init__(self, config: Optional[SplitterConfig] = None, logger: Optional[LoggerService] = None):
        """初始化切分器
        
        Args:
            config: 切分器配置
        """
        pass
    
    @abstractmethod
    def split_document(self, document: Document) -> List[DocumentChunk]:
        """切分单个文档
        
        Args:
            document: 要切分的文档
            
        Returns:
            文档块列表
        """
        pass
    
    @abstractmethod
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """切分文本
        
        Args:
            text: 要切分的文本
            metadata: 元数据
            
        Returns:
            文档块列表
        """
        pass
    
    @abstractmethod
    def get_splitter_type(self) -> SplitterType:
        """获取切分器类型
        
        Returns:
            切分器类型
        """
        pass
    
    def split_documents(self, documents: List[Document]) -> List[DocumentChunk]:
        """切分多个文档
        
        Args:
            documents: 文档列表
            
        Returns:
            所有文档块列表
        """
        all_chunks = []
        for document in documents:
            chunks = self.split_document(document)
            all_chunks.extend(chunks)
        return all_chunks
    
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            配置是否有效
        """
        if self.config.chunk_size <= 0:
            return False
        
        if self.config.chunk_overlap < 0:
            return False
        
        if self.config.chunk_overlap >= self.config.chunk_size:
            return False
        
        return True
    
    def get_config(self) -> SplitterConfig:
        """获取配置
        
        Returns:
            切分器配置
        """
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """更新配置
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def _create_chunk(
        self,
        content: str,
        chunk_index: int,
        start_char: int = 0,
        parent_doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentChunk:
        """创建文档块
        
        Args:
            content: 块内容
            chunk_index: 块索引
            start_char: 起始字符位置
            parent_doc_id: 父文档ID
            metadata: 元数据
            
        Returns:
            文档块
        """
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata.update({
            'splitter_type': self.get_splitter_type().value,
            'chunk_size_config': self.config.chunk_size,
            'chunk_overlap_config': self.config.chunk_overlap
        })
        
        return DocumentChunk(
            content=content,
            metadata=chunk_metadata,
            parent_doc_id=parent_doc_id,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=start_char + len(content),
            chunk_size=len(content),
            overlap_size=self.config.chunk_overlap if chunk_index > 0 else 0
        )
    
    def _clean_content(self, content: str) -> str:
        """清理内容
        
        Args:
            content: 原始内容
            
        Returns:
            清理后的内容
        """
        if self.config.strip_whitespace:
            content = content.strip()
        
        # 移除多余的空行
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            if not (is_empty and prev_empty):
                cleaned_lines.append(line)
            prev_empty = is_empty
        
        return '\n'.join(cleaned_lines)
    
    def get_chunk_count_estimate(self, text: str) -> int:
        """估算文档块数量
        
        Args:
            text: 文本内容
            
        Returns:
            估算的块数量
        """
        text_length = len(text)
        if text_length <= self.config.chunk_size:
            return 1
        
        effective_chunk_size = self.config.chunk_size - self.config.chunk_overlap
        return max(1, (text_length - self.config.chunk_size) // effective_chunk_size + 1)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(type={self.get_splitter_type().value}, chunk_size={self.config.chunk_size})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"{self.__class__.__name__}(config={self.config.to_dict()})")

class DocumentSplitterService(ABC):
    """文档切分服务接口
    
    定义文档切分的核心业务逻辑
    """
    
    @abstractmethod
    def should_split_document(self, document: Document) -> bool:
        """判断文档是否需要切分
        
        Args:
            document: 要判断的文档
            
        Returns:
            bool: 是否需要切分
        """
        pass


class DocumentSplitterServiceAdapter(DocumentSplitterService):
    """领域层服务适配器

    封装调用基础设施层 `DocumentSplitterServiceImpl`，并在需要时将参数转换为
    `infrastructure.splitters.types` 中的同构类型。
    """

    def __init__(self, long_document_threshold: int = 10, logger: Optional[LoggerService] = None):
        # 延迟导入避免循环依赖
        from ...infrastructure.splitters.document_splitter_service_impl import DocumentSplitterServiceImpl

        self.logger = logger
        self._impl = DocumentSplitterServiceImpl(long_document_threshold, logger)

    async def should_split_document(self, document: Document) -> bool:
        # 直接委托基础设施层实现（其内部基于长度与结构判断）
        return await self._impl.should_split_document(document)

    async def split_document(
        self,
        document: Document,
    ) -> List[DocumentChunk]:
        # 直接委托基础设施层实现（其内部负责选择具体切分器并完成实体转换）
        return await self._impl.split_document(document)

    # ---------- 参数转换工具（供需要在调用前进行类型映射的场景使用） ----------
    @staticmethod
    def to_infra_document(doc: Document):
        """将领域层 Document 转为基础设施层 InfraDocument"""
        from ...infrastructure.splitters.types import InfraDocument
        return InfraDocument(
            content=doc.content,
            metadata=doc.metadata,
            doc_id=doc.doc_id,
            doc_type=doc.doc_type,
            source_path=doc.source_path,
            created_at=doc.created_at,
        )

    @staticmethod
    def to_infra_config(config: SplitterConfig):
        """将领域层 SplitterConfig 转为基础设施层 InfraSplitterConfig"""
        from ...infrastructure.splitters.types import InfraSplitterConfig
        return InfraSplitterConfig.from_dict(config.to_dict())
    
    @abstractmethod
    def split_document(
        self, 
        document: Document, 
    ) -> List[DocumentChunk]:
        """切分文档
        
        Args:
            document: 要切分的文档
            splitter_type: 切分器类型
            config: 切分配置
            
        Returns:
            List[DocumentChunk]: 切分后的文档块列表
        """
        pass
    
    @abstractmethod
    def has_complex_structure(self, document: Document) -> bool:
        """检查文档是否有复杂结构
        
        Args:
            document: 要检查的文档
            
        Returns:
            bool: 是否有复杂结构
        """
        pass
