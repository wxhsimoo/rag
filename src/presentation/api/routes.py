from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pathlib import Path
import json
from pydantic import BaseModel, Field
from ..container import get_app_container
from ...domain.entities.qa_context import UserProfile
from ...domain.entities.document import Document
from ..service_factory import DDDServiceFactory
from ...infrastructure.config.config_manager import Config

router = APIRouter()

# 请求模型
class UserProfileRequest(BaseModel):
    """用户档案请求模型"""
    user_id: str
    baby_age_months: Optional[int] = None
    baby_name: Optional[str] = None
    known_allergens: List[str] = field(default_factory=list)
    dietary_preferences: List[str] = field(default_factory=list)
    feeding_history: List[str] = field(default_factory=list)
    special_needs: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class QueryRequest(BaseModel):
    """查询请求模型"""
    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)
    user_profile: Optional[UserProfileRequest] = Field(None, description="用户档案")
    session_id: Optional[str] = Field(None, description="会话ID")
    top_k: Optional[int] = Field(5, description="返回的相关文档数量", ge=1, le=20)

# 响应模型
class SourceDocument(BaseModel):
    """来源文档模型"""
    id: str = Field(..., description="文档ID")
    content: str = Field(..., description="文档内容")
    score: float = Field(..., description="相关性分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")

class QueryResponse(BaseModel):
    """查询响应模型"""
    success: bool = Field(..., description="是否成功")
    answer: str = Field(..., description="回答")
    structured_response: Optional[Dict[str, Any]] = Field(None, description="结构化响应")
    sources: List[SourceDocument] = Field(default_factory=list, description="来源文档")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="用户档案")
    session_id: Optional[str] = Field(None, description="会话ID")
    processing_time: float = Field(..., description="处理时间（秒）")
    timestamp: str = Field(..., description="时间戳")
    error: Optional[str] = Field(None, description="错误信息")

# 文档管理请求模型
class DocumentRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    doc_id: Optional[str] = None
    doc_type: Optional[str] = None
    source_path: Optional[str] = None

class DocumentUpdateRequest(DocumentRequest):
    """更新请求与保存一致，保留相同字段"""
    pass

class PaginationQuery(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)
    category: Optional[str] = None

# 辅助函数
def convert_user_profile(profile_request: Optional[UserProfileRequest]) -> Optional[UserProfile]:
    """转换用户档案请求为领域对象
    
    Args:
        profile_request: 用户档案请求
        
    Returns:
        用户档案领域对象
    """
    if not profile_request:
        return None
    
    return UserProfile(
        user_id=profile_request.user_id,
    )

# API路由
@router.post("/query", response_model=QueryResponse, summary="RAG查询")
async def rag_query(
    request: QueryRequest,
):
    """RAG查询
    
    处理用户的咨询问题，基于知识库返回专业建议。
    
    Args:
        request: 查询请求
        
    Returns:
        查询结果
        
    Raises:
        HTTPException: 查询处理失败时抛出
    """
    try:
        # 转换用户档案
        user_profile = convert_user_profile(request.user_profile)
        print(user_profile)
        # 调用RAG管道服务
        container = get_app_container()
        result = await container._rag_pipeline_service.query(
            question=request.question,
            user_profile=user_profile,
            session_id=request.session_id,
            top_k=request.top_k,
           )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "查询处理失败")
            )
        
        # 转换响应格式
        sources = [
            SourceDocument(
                id=source["id"],
                content=source["content"],
                score=source["score"],
                metadata=source["metadata"]
            )
            for source in result.get("sources", [])
        ]
        
        return QueryResponse(
            success=True,
            answer=result["answer"],
            structured_response=result.get("structured_response"),
            sources=sources,
            user_profile=result.get("user_profile"),
            session_id=result.get("session_id"),
            processing_time=result["processing_time"],
            timestamp=result["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询处理失败: {str(e)}"
        )

# 文档管理接口
@router.get("/documents", summary="列出文档")
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
):
    
    container = get_app_container()
    svc = container._document_storage_management_service
    result = await svc.list_documents(category=category)
    return result

@router.get("/documents/{doc_id}", summary="获取文档详情")
async def get_document(doc_id: str, container = Depends(get_app_container)):
    container = get_app_container()
    svc = container._document_storage_management_service
    doc = await svc.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {
        "doc_id": doc.doc_id,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }

@router.post("/documents", summary="保存文档（multipart/form-data 上传文件）")
async def save_document(
    file: UploadFile = File(...),
    doc_type: Optional[str] = Form(None),
    source_path: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    container = Depends(get_app_container),
):
    # 读取上传文件内容
    try:
        content_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取上传文件失败: {e}")

    # 根据文件后缀判断是否二进制类型，二进制类型不做解码，避免失真
    from pathlib import Path
    import base64
    suffix = Path(file.filename).suffix.lower()
    BINARY_SUFFIXES = {'.pdf', '.docx', '.pptx', '.xlsx'}
    is_binary = suffix in BINARY_SUFFIXES
    if is_binary:
        content_text = ""  # 保持原始字节，通过元数据传递
    else:
        # 文本类型尝试解码
        try:
            content_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_text = content_bytes.decode("latin-1", errors="ignore")

    # 解析 metadata（JSON 字符串或留空）
    meta_obj: Dict[str, Any] = {}
    if metadata:
        try:
            meta_obj = json.loads(metadata)
        except Exception:
            meta_obj = {"_raw_metadata": metadata}

    # 补充通用文件信息与二进制标记
    meta_obj.setdefault("file_size", len(content_bytes))
    meta_obj.setdefault("file_extension", suffix)
    if is_binary:
        # 将原始字节以base64写入元数据，供存储端二进制直写
        meta_obj["_is_binary"] = True
        meta_obj["_binary_base64"] = base64.b64encode(content_bytes).decode("ascii")

    # 使用上传文件名作为默认保存文件名
    final_source_path = source_path or file.filename

    container = get_app_container()
    svc = container._document_storage_management_service
    doc = Document(
        content=content_text,
        metadata=meta_obj,
        doc_type=doc_type or suffix,
        source_path=final_source_path,
        created_at=datetime.now(),
    )
    ok, doc_id = await svc.save_document(doc)
    if not ok:
        raise HTTPException(status_code=400, detail="文档保存失败（校验未通过或存储错误）")
    return {"success": True, "doc_id": doc_id}

@router.delete("/documents/{doc_id}", summary="删除文档")
async def delete_document(doc_id: str, container = Depends(get_app_container)):
    container = get_app_container()
    svc = container._document_storage_management_service
    ok = await svc.delete_document(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="删除失败，文档不存在或存储错误")
    return {"success": True, "doc_id": doc_id}

# 索引初始化接口（无需入参）
@router.post("/index/init", summary="初始化向量索引")
async def init_vector_index():
    """初始化向量索引：
    - 自动收集本地文档目录下支持的文件类型
    - 构建或重建向量索引
    - 无需任何入参
    """
    container = get_app_container()
    logger = getattr(container, "logger", None)
    start_time = datetime.now()
    if logger:
        logger.info("[API] /index/init 请求进入，开始初始化向量索引")
    
    # 获取服务
    svcIndexing = container._indexing_service
    doc_svc = container._document_storage_management_service

    # 获取文件
    if logger:
        logger.info("[API] /index/init 开始列出待索引文档")
    items = await doc_svc.list_documents()
    if logger:
        logger.info(f"[API] /index/init 文档列表获取完成，数量={len(items)}")

    base_path = Path(container.config.storage.documents.local.base_path)
    file_paths: List[str] = []
    for item in items:
        filename = item.get("filename")

        if not filename:
            continue
        full_path = base_path / filename
        if logger:
            logger.debug(f"[API] /index/init 发现文件: {full_path}")
        file_paths.append(str(full_path))

    # 若没有可用文件，直接返回提示
    if not file_paths:
        if logger:
            logger.warning("[API] /index/init 未发现可用于索引的文件，直接返回")
        return {
            "success": True,
            "message": "未找到可用于索引的支持文件",
            "documents_processed": 0,
            "processing_time": 0
        }

    # 构建索引（初始化通常重建索引）
    if logger:
        logger.info(f"[API] /index/init 开始构建索引，文件数={len(file_paths)}，force_rebuild=True")
    try:
        result = await svcIndexing.build_index(file_paths, force_rebuild=True)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        if logger:
            logger.info(
                f"[API] /index/init 索引构建完成：success={result.get('success')}, processed={result.get('documents_processed')}, "
                f"processing_time={result.get('processing_time')}s, api_duration={duration}s"
            )
        return result
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        if logger:
            logger.error(f"[API] /index/init 索引构建异常：{str(e)}，api_duration={duration}s")
        raise
