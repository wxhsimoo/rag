from typing import List, Dict, Any, Optional

try:
    from langchain_community.document_loaders import TextLoader as LangchainTextLoader
except ImportError:
    LangchainTextLoader = None

from ...infrastructure.log.logger_service import LoggerService
from ..splitters.types import InfraDocument
from .base import InfraDocumentLoader


class TextDocumentLoader(InfraDocumentLoader):
    """纯文本文件加载器，支持 `.txt` 和 `.text`。"""

    def __init__(self, logger: Optional[LoggerService] = None, encoding: str = "utf-8"):
        self.logger = logger
        self.encoding = encoding

    def supports_file_type(self, file_path: str) -> bool:
        ext = file_path.lower().split('.')[-1]
        return ext in ["txt", "text"]

    def get_supported_extensions(self) -> List[str]:
        return ["txt", "text"]

    def load(self, file_path: str) -> List[InfraDocument]:
        return self._load_documents(file_path)

    def _create_document(self, content: str, metadata: Dict[str, Any] = None) -> InfraDocument:
        if metadata is None:
            metadata = {}
        return InfraDocument(content=content, metadata=metadata)

    def _clean_content(self, content: str) -> str:
        if not content:
            return ""
        content = content.strip()
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        return content

    def _load_documents(self, file_path: str) -> List[InfraDocument]:
        if LangchainTextLoader is not None:
            return self._load_with_langchain(file_path)
        return self._load_with_builtin(file_path)

    def _load_with_langchain(self, file_path: str) -> List[InfraDocument]:
        try:
            loader = LangchainTextLoader(file_path, encoding=self.encoding)
            lc_docs = loader.load()
            documents: List[Document] = []
            for lc in lc_docs:
                metadata = dict(lc.metadata) if lc.metadata else {}
                doc = self._create_document(content=self._clean_content(lc.page_content), metadata=metadata)
                documents.append(doc)
            return documents
        except Exception as e:
            if self.logger:
                self.logger.warning(f"使用 TextLoader 加载失败，回退到内置实现: {e}")
            return self._load_with_builtin(file_path)

    def _load_with_builtin(self, file_path: str) -> List[InfraDocument]:
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            content = self._clean_content(content)
            if not content:
                return []
            meta = {
                "type": "text_file",
                "source": str(file_path),
                "size": len(content),
            }
            return [self._create_document(content=content, metadata=meta)]
        except Exception as e:
            raise ValueError(f"加载文本文件失败: {e}")
