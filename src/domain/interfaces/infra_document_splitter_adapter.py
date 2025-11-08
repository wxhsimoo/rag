from typing import List, Dict, Any, Optional

from .document_splitter_service import DocumentSplitter, SplitterType, SplitterConfig
from ..entities.document import Document
from ..entities.document_chunk import DocumentChunk
from ...infrastructure.log.logger_service import LoggerService

from ...infrastructure.splitters.base import InfraDocumentSplitter
from ...infrastructure.splitters.types import (
    InfraDocument,
    InfraDocumentChunk,
    InfraSplitterConfig,
)


class InfraDocumentSplitterAdapter(DocumentSplitter):
    """领域层适配器：包装基础设施层切分器，提供领域层接口

    在调用时进行数据结构转换，确保领域层仅与领域实体交互。
    """

    def __init__(self, infra_splitter: InfraDocumentSplitter, logger: Optional[LoggerService] = None):
        self.infra_splitter = infra_splitter
        self.logger = logger
        # 将基础设施配置映射为领域层配置（保持一致字段）
        self.config = SplitterConfig.from_dict(self.infra_splitter.get_config().to_dict())

    def get_splitter_type(self) -> SplitterType:
        # 通过枚举值映射为领域层类型
        return SplitterType(self.infra_splitter.get_splitter_type().value)

    def split_document(self, document: Document) -> List[DocumentChunk]:
        infra_doc = self._to_infra_document(document)
        infra_chunks = self.infra_splitter.split_document(infra_doc)
        return [self._to_domain_chunk(c) for c in infra_chunks]

    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        infra_chunks = self.infra_splitter.split_text(text, metadata)
        return [self._to_domain_chunk(c) for c in infra_chunks]

    # ---------- 转换工具方法 ----------
    @staticmethod
    def _to_infra_document(doc: Document) -> InfraDocument:
        return InfraDocument(
            content=doc.content,
            metadata=doc.metadata,
            doc_id=doc.doc_id,
            doc_type=doc.doc_type,
            source_path=doc.source_path,
            created_at=doc.created_at,
        )

    @staticmethod
    def _to_domain_chunk(chunk: InfraDocumentChunk) -> DocumentChunk:
        return DocumentChunk(
            content=chunk.content,
            metadata=chunk.metadata,
            chunk_id=chunk.chunk_id,
            parent_doc_id=chunk.parent_doc_id,
            chunk_index=chunk.chunk_index,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            chunk_size=chunk.chunk_size,
            overlap_size=chunk.overlap_size,
            created_at=chunk.created_at,
        )

