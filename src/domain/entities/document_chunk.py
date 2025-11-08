from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class DocumentChunk:
    """文档块实体
    
    表示文档切分后的单个片段
    """
    
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
        """初始化后处理"""
        if not self.chunk_size:
            self.chunk_size = len(self.content)
        
        if not self.end_char and self.start_char:
            self.end_char = self.start_char + len(self.content)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值
        """
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """批量更新元数据
        
        Args:
            metadata: 元数据字典
        """
        self.metadata.update(metadata)
    
    def is_empty(self) -> bool:
        """检查是否为空块
        
        Returns:
            是否为空
        """
        return not self.content or not self.content.strip()
    
    def get_text_length(self) -> int:
        """获取文本长度
        
        Returns:
            文本长度
        """
        return len(self.content) if self.content else 0
    
    def get_char_range(self) -> tuple[int, int]:
        """获取字符范围
        
        Returns:
            (起始位置, 结束位置)
        """
        return self.start_char, self.end_char
    
    def has_overlap(self) -> bool:
        """检查是否有重叠
        
        Returns:
            是否有重叠
        """
        return self.overlap_size > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentChunk':
        """从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            DocumentChunk实例
        """
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
            created_at=created_at or datetime.now()
        )
    
    def __str__(self) -> str:
        """字符串表示"""
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"DocumentChunk(id={self.chunk_id[:8]}, size={self.chunk_size}, content='{preview}')"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"DocumentChunk(chunk_id='{self.chunk_id}', "
                f"parent_doc_id='{self.parent_doc_id}', "
                f"chunk_index={self.chunk_index}, "
                f"size={self.chunk_size})")