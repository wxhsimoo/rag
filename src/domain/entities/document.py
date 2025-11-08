from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class Document:
    """文档实体类
    
    统一的文档数据结构，用于表示从不同来源加载的文档
    """
    
    # 文档内容
    content: str
    
    # 文档元数据
    metadata: Dict[str, Any]
    
    # 文档唯一标识
    doc_id: Optional[str] = None
    
    # 文档类型（json, markdown等）
    doc_type: Optional[str] = None
    
    # 文档来源文件路径
    source_path: Optional[str] = None
    
    # 创建时间
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """获取元数据值
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            元数据值或默认值
        """
        return self.metadata.get(key, default)
    
    def set_metadata_value(self, key: str, value: Any) -> None:
        """设置元数据值
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            文档的字典表示
        """
        return {
            'doc_id': self.doc_id,
            'content': self.content,
            'metadata': self.metadata,
            'doc_type': self.doc_type,
            'source_path': self.source_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }