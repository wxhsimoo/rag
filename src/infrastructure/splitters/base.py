from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from .types import (
    InfraDocument,
    InfraDocumentChunk,
    InfraSplitterType,
    InfraSplitterConfig,
)
from ...infrastructure.log.logger_service import LoggerService


class InfraDocumentSplitter(ABC):
    """基础设施层的文档切分器抽象基类

    与领域层接口保持方法一致，但仅使用基础设施层的数据结构。
    """

    def __init__(self, config: Optional[InfraSplitterConfig] = None, logger: Optional[LoggerService] = None):
        self.config = config or InfraSplitterConfig()
        self.logger = logger

    @abstractmethod
    def split_document(self, document: InfraDocument) -> List[InfraDocumentChunk]:
        pass

    @abstractmethod
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[InfraDocumentChunk]:
        pass

    @abstractmethod
    def get_splitter_type(self) -> InfraSplitterType:
        pass

    def split_documents(self, documents: List[InfraDocument]) -> List[InfraDocumentChunk]:
        all_chunks: List[InfraDocumentChunk] = []
        for document in documents:
            chunks = self.split_document(document)
            all_chunks.extend(chunks)
        return all_chunks

    def validate_config(self) -> bool:
        if self.config.chunk_size <= 0:
            return False
        if self.config.chunk_overlap < 0:
            return False
        if self.config.chunk_overlap >= self.config.chunk_size:
            return False
        return True

    def get_config(self) -> InfraSplitterConfig:
        return self.config

    def update_config(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def _create_chunk(
        self,
        content: str,
        chunk_index: int,
        start_char: int = 0,
        parent_doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InfraDocumentChunk:
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata.update({
            'splitter_type': self.get_splitter_type().value,
            'chunk_size_config': self.config.chunk_size,
            'chunk_overlap_config': self.config.chunk_overlap,
        })

        return InfraDocumentChunk(
            content=content,
            metadata=chunk_metadata,
            parent_doc_id=parent_doc_id,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=start_char + len(content),
            chunk_size=len(content),
            overlap_size=self.config.chunk_overlap if chunk_index > 0 else 0,
        )

    def _clean_content(self, content: str) -> str:
        if self.config.strip_whitespace:
            content = content.strip()
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
        if not text:
            return 0
        length = len(text)
        size = max(1, self.config.chunk_size)
        overlap = max(0, self.config.chunk_overlap)
        if overlap >= size:
            return 1
        # 估算：考虑重叠后的有效步长
        step = size - overlap
        return max(1, (length + step - 1) // step)

