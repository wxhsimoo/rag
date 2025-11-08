from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ...domain.interfaces.document_storage_service import DocumentStorageService

@dataclass
class RawDocument:
    """原始文档数据类"""
    id: str
    content: str
    source: str  # 文档来源（本地路径或 s3://bucket/key）
    metadata: Dict[str, Any] = None

class DocumentStorageProvider(DocumentStorageService, ABC):
    """文档存储接口（基础抽象类）
    仅定义必须的 Raw 层抽象方法，具体 Domain 层实现交由各 Provider 完成。
    """

    # --------------------
    # Raw 层抽象方法（具体实现必须覆盖）
    # --------------------
    @abstractmethod
    async def _load_raw_documents(self, source_path: Optional[str] = None) -> List[RawDocument]:
        """加载所有原始文档（可按源路径/前缀过滤）"""
        pass

    @abstractmethod
    async def _save_raw_document(self, document: RawDocument) -> bool:
        """保存原始文档"""
        pass

    @abstractmethod
    async def _get_raw_document(self, document_id: str) -> Optional[RawDocument]:
        """获取原始文档"""
        pass

    @abstractmethod
    async def _delete_raw_document(self, document_id: str) -> bool:
        """删除原始文档"""
        pass

    @abstractmethod
    async def _list_raw_documents(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出原始文档信息（至少包含 id/source/metadata）"""
        pass

    # 仅保留 Raw 层抽象方法，Domain 层接口方法由具体 Provider 实现
