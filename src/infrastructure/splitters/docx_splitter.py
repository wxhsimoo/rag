from typing import List, Dict, Any, Optional

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from ...infrastructure.log.logger_service import LoggerService
from .types import InfraDocument, InfraDocumentChunk, InfraSplitterType, InfraSplitterConfig
from .base import InfraDocumentSplitter


class DocxSplitter(InfraDocumentSplitter):
    """DOCX 文本切分器

    DOCX 已在加载阶段转为纯文本，此切分器对文本进行分段。
    优先使用 Langchain 的 RecursiveCharacterTextSplitter，无法使用时回退到简单字符/段落切分。
    """

    def __init__(self, config: Optional[InfraSplitterConfig] = None, logger: Optional[LoggerService] = None):
        self.logger = logger
        self.config = config or InfraSplitterConfig()
        self.text_splitter = None
        self._init_langchain_splitter()

    def _init_langchain_splitter(self) -> None:
        if LANGCHAIN_AVAILABLE:
            try:
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap,
                    separators=self.config.separators or ["\n\n", "\n", " ", ""],
                    keep_separator=self.config.keep_separator,
                    add_start_index=self.config.add_start_index,
                    strip_whitespace=self.config.strip_whitespace,
                )
                if self.logger:
                    self.logger.info("Initialized Langchain RecursiveCharacterTextSplitter for DocxSplitter")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to initialize Langchain DOCX splitter: {str(e)}")
                self.text_splitter = None

    def get_splitter_type(self) -> InfraSplitterType:
        return InfraSplitterType.RECURSIVE_CHARACTER

    def split_document(self, document: InfraDocument) -> List[InfraDocumentChunk]:
        metadata = {
            'source': document.source_path,
            'document_id': document.doc_id,
            'file_type': document.doc_type,
            'created_at': document.created_at.isoformat() if document.created_at else None,
        }
        return self.split_text(document.content, metadata)

    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[InfraDocumentChunk]:
        if metadata is None:
            metadata = {}
        return self._split_text_impl(text, metadata)

    def _split_text_impl(self, text: str, metadata: Dict[str, Any]) -> List[InfraDocumentChunk]:
        if LANGCHAIN_AVAILABLE and self.text_splitter:
            return self._split_with_langchain(text, metadata)
        else:
            return self._split_with_fallback(text, metadata)

    def _split_with_langchain(self, text: str, metadata: Dict[str, Any]) -> List[InfraDocumentChunk]:
        try:
            docs = self.text_splitter.create_documents([text], [metadata])
            chunks: List[InfraDocumentChunk] = []
            for i, d in enumerate(docs):
                chunk = self._create_chunk_from_text(
                    content=d.page_content,
                    chunk_index=i,
                    start_char=0,
                    metadata=metadata,
                )
                chunk.set_metadata('docx_method', 'langchain_recursive_character')
                chunks.append(chunk)
            if self.logger:
                self.logger.debug(f"Langchain split DOCX text into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in Langchain DOCX splitting: {str(e)}")
            return self._split_with_fallback(text, metadata)

    def _split_with_fallback(self, text: str, metadata: Dict[str, Any]) -> List[InfraDocumentChunk]:
        chunks: List[InfraDocumentChunk] = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        # DOCX 常见段落分隔为两个换行
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            current_chunk = ""
            for paragraph in paragraphs:
                candidate = (current_chunk + "\n\n" + paragraph) if current_chunk else paragraph
                if len(candidate) <= chunk_size:
                    current_chunk = candidate
                else:
                    if current_chunk.strip():
                        chunk = self._create_chunk_from_text(
                            content=current_chunk.strip(),
                            chunk_index=len(chunks),
                            start_char=0,
                            metadata=metadata,
                        )
                        chunk.set_metadata('docx_method', 'fallback_paragraph')
                        chunks.append(chunk)
                    current_chunk = paragraph
            if current_chunk.strip():
                chunk = self._create_chunk_from_text(
                    content=current_chunk.strip(),
                    chunk_index=len(chunks),
                    start_char=0,
                    metadata=metadata,
                )
                chunk.set_metadata('docx_method', 'fallback_paragraph')
                chunks.append(chunk)
        else:
            # 强制按字符切分
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                content = text[start:end]
                if content.strip():
                    chunk = self._create_chunk_from_text(
                        content=content,
                        chunk_index=len(chunks),
                        start_char=start,
                        metadata=metadata,
                    )
                    chunk.set_metadata('docx_method', 'fallback_character')
                    chunks.append(chunk)
                start = end - overlap
                if start <= 0:
                    start = end
        if self.logger:
            self.logger.debug(f"Fallback split DOCX text into {len(chunks)} chunks")
        return chunks

    def _create_chunk_from_text(
        self,
        content: str,
        chunk_index: int,
        start_char: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InfraDocumentChunk:
        return self._create_chunk(
            content=content,
            chunk_index=chunk_index,
            start_char=start_char,
            metadata=metadata,
        )
