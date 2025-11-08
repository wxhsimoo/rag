from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
import uuid


class InfraSplitterType(Enum):
    """基础设施层的切分器类型枚举，与领域层保持一致的值"""
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
class InfraSplitterConfig:
    """基础设施层的切分器配置，字段与领域层保持一致"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: Optional[List[str]] = None
    keep_separator: bool = True
    add_start_index: bool = True
    strip_whitespace: bool = True

    similarity_threshold: float = 0.5
    min_chunk_size: int = 100
    max_chunk_size: int = 2000

    custom_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}

    def to_dict(self) -> Dict[str, Any]:
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
            'custom_params': self.custom_params,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InfraSplitterConfig':
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
            custom_params=data.get('custom_params', {}),
        )


@dataclass
class InfraDocument:
    """基础设施层的文档结构，与领域层 Document 对齐"""
    content: str
    metadata: Dict[str, Any]
    doc_id: Optional[str] = None
    doc_type: Optional[str] = None
    source_path: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def set_metadata_value(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            'doc_id': self.doc_id,
            'content': self.content,
            'metadata': self.metadata,
            'doc_type': self.doc_type,
            'source_path': self.source_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class InfraDocumentChunk:
    """基础设施层的文档块结构，与领域层 DocumentChunk 对齐"""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_doc_id: Optional[str] = None
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 0
    chunk_size: int = 0
    overlap_size: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.chunk_size:
            self.chunk_size = len(self.content)
        if not self.end_char and self.start_char:
            self.end_char = self.start_char + len(self.content)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        self.metadata.update(metadata)

    def is_empty(self) -> bool:
        return not self.content or not self.content.strip()

    def get_text_length(self) -> int:
        return len(self.content) if self.content else 0

    def get_char_range(self) -> tuple[int, int]:
        return self.start_char, self.end_char

    def has_overlap(self) -> bool:
        return self.overlap_size > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'metadata': self.metadata,
            'parent_doc_id': self.parent_doc_id,
            'chunk_index': self.chunk_index,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'chunk_size': self.chunk_size,
            'overlap_size': self.overlap_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InfraDocumentChunk':
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        return cls(
            content=data['content'],
            metadata=data.get('metadata', {}),
            chunk_id=data.get('chunk_id', str(uuid.uuid4())),
            parent_doc_id=data.get('parent_doc_id'),
            chunk_index=data.get('chunk_index', 0),
            start_char=data.get('start_char', 0),
            end_char=data.get('end_char', 0),
            chunk_size=data.get('chunk_size', 0),
            overlap_size=data.get('overlap_size', 0),
            created_at=created_at or datetime.now(),
        )

