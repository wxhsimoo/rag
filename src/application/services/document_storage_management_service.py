from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ...domain.interfaces.document_storage_service import DocumentStorageService
from typing import Tuple
from ...domain.entities.document import Document


class DocumentStorageManagementService:
    """文档存储管理服务
    
    封装基于 DocumentStorageService 的常用文档管理操作：
    - 基础 CRUD（加载、保存、获取、更新、删除、列表、搜索、统计）
    - 批量保存
    - Upsert（存在则更新，不存在则创建）
    - 分页
    - 校验与支持格式查询
    """

    def __init__(self, repo: DocumentStorageService, logger: Optional[Any] = None):
        """初始化服务
        
        Args:
            repo: 文档仓储接口实现
            logger: 可选的日志记录器，需支持 info/warning/error 等方法
        """
        self._repo = repo
        self._logger = logger or logging.getLogger("FileManagementService")

    async def load_documents(self, source_path: Optional[str] = None) -> List[Document]:
        """加载文档（可选指定源路径）"""
        self._logger.info("Loading documents from: %s", source_path or "<all>")
        docs = await self._repo.load_documents(source_path=source_path)
        self._logger.info("Loaded %d documents", len(docs))
        return docs

    async def save_document(self, document: Document) -> Tuple[bool, str]:
        """保存单个文档，返回 (是否成功, 文档ID)"""
        # 补全创建时间
        if not document.created_at:
            document.created_at = datetime.now()
        ok, doc_id = await self._repo.save_document(document)
        # 若保存成功且 document.doc_id 为空，则补回生成的 doc_id
        if ok and not document.doc_id:
            document.doc_id = doc_id
        self._logger.info("Saved document [%s]: %s", document.doc_id or doc_id or "<no-id>", ok)
        return ok, (doc_id or (document.doc_id or ""))

    async def get_document(self, document_id: str) -> Optional[Document]:
        """根据ID获取文档"""
        doc = await self._repo.get_document(document_id)
        self._logger.info("Get document [%s]: %s", document_id, "found" if doc else "not-found")
        return doc

    async def list_documents(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出文档（返回信息字典列表）"""
        items = await self._repo.list_documents(category=category)
        self._logger.info("List documents (category=%s): %d", category, len(items))
        return items

    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        ok = await self._repo.delete_document(document_id)
        self._logger.info("Delete document [%s]: %s", document_id, ok)
        return ok

    async def search_documents(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Document]:
        """搜索文档"""
        results = await self._repo.search_documents(query=query, category=category, limit=limit)
        self._logger.info("Search documents (query=%s, category=%s, limit=%d): %d", query, category, limit, len(results))
        return results

    async def get_document_count(self, category: Optional[str] = None) -> int:
        """获取文档数量（可按分类）"""
        count = await self._repo.get_document_count(category=category)
        self._logger.info("Document count (category=%s): %d", category, count)
        return count

    async def update_document(self, document: Document) -> bool:
        """更新文档"""
        if not await self._repo.validate_document(document):
            self._logger.warning("Document validation failed on update: %s", document.doc_id or "<no-id>")
            return False
        ok = await self._repo.update_document(document)
        self._logger.info("Update document [%s]: %s", document.doc_id or "<no-id>", ok)
        return ok

    def get_supported_formats(self) -> List[str]:
        """获取支持的文档格式"""
        formats = self._repo.get_supported_formats()
        self._logger.info("Supported formats: %s", formats)
        return formats

    async def validate_document(self, document: Document) -> bool:
        """验证文档"""
        ok = await self._repo.validate_document(document)
        self._logger.info("Validate document [%s]: %s", document.doc_id or "<no-id>", ok)
        return ok

    async def save_documents_bulk(self, documents: List[Document]) -> int:
        """批量保存文档，返回成功数量"""
        success = 0
        for doc in documents:
            ok, _ = await self.save_document(doc)
            if ok:
                success += 1
        self._logger.info("Bulk saved %d/%d documents", success, len(documents))
        return success

    async def upsert_document(self, document: Document) -> bool:
        """Upsert 文档：存在则更新，不存在则创建"""
        if not document.doc_id:
            # 若无 doc_id，直接作为新建
            ok, _ = await self.save_document(document)
            return ok

        existing = await self._repo.get_document(document.doc_id)
        if existing:
            return await self.update_document(document)
        ok, _ = await self.save_document(document)
        return ok

    async def paginate_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """文档分页（基于 list_documents 的简单切片）
        
        返回:
            {
                "items": List[Dict[str, Any]],
                "total": int,
                "page": int,
                "page_size": int,
                "pages": int
            }
        """
        if page <= 0:
            page = 1
        if page_size <= 0:
            page_size = 20

        total = await self.get_document_count(category=category)
        items = await self.list_documents(category=category)

        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]

        pages = (total + page_size - 1) // page_size
        result = {
            "items": page_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }
        self._logger.info(
            "Paginate documents (category=%s): page=%d, size=%d, total=%d, pages=%d, returned=%d",
            category, page, page_size, total, pages, len(page_items)
        )
        return result

    async def exists(self, document_id: str) -> bool:
        """判断文档是否存在"""
        return (await self.get_document(document_id)) is not None
