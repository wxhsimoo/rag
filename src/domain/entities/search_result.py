from typing import Dict, Any, Optional
from .document import Document


class SearchResult:
    """搜索结果实体，包含文档、分数及附加元数据。"""

    def __init__(self, document: Document, score: float, metadata: Optional[Dict[str, Any]] = None):
        self.document = document
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "metadata": self.metadata,
        }

