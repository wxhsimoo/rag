"""Domain层接口定义

本模块定义了系统的核心接口，遵循DDD原则：
- Domain层只关心抽象，不依赖具体技术
- Infrastructure层实现这些抽象
- Application层依赖抽象，通过依赖注入调用
"""

from .document_storage_service import DocumentStorageService
from .embedding_service import EmbeddingService
from .llm_service import LLMService
from .vector_store_service import VectorStoreService
from .document_splitter_service import DocumentSplitterService
from ..entities.search_result import SearchResult

# 已移除的接口文件，现在直接使用application层实现


__all__ = [
    "DocumentRepository",
    "EmbeddingService", 
    "LLMService",
    "VectorStoreService",
    "SearchResult",
    "DocumentSplitterService"
]
