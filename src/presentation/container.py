from typing import Optional, Dict, Any
import sys
from loguru import logger
from functools import lru_cache

from ..infrastructure.log.logger_service import LoggerService
from ..infrastructure.config.config_manager import Config, get_config
from .service_factory import DDDServiceFactory
from ..application.services.rag_pipeline_service import RAGPipelineService
from ..application.services.indexing_service import IndexingService
from ..application.services.document_storage_management_service import DocumentStorageManagementService


class ApplicationContainer:
    """应用容器 - 依赖注入和服务管理"""
    config: Config
    logger: LoggerService
    _rag_pipeline_service: Optional[RAGPipelineService] = None
    _document_storage_management_service: Optional[DocumentStorageManagementService] = None
    _indexing_service: Optional[IndexingService] = None

    def __init__(self, config: Optional[Config] = None, logger: Optional[LoggerService] = None):
        # 迁移自 run.py 的配置加载与日志初始化
        if config is None:
            config = get_config()
        self.config = config

        # 基于配置初始化全局日志（loguru）
        try:
            self._setup_global_logging(self.config)
        except Exception:
            # 日志初始化失败不阻塞启动，仅输出到控制台
            pass

        # 初始化应用层日志服务
        self.logger = logger
        try:
            service_factory = DDDServiceFactory(config)
            self._rag_pipeline_service  = service_factory.create_application_rag_pipeline_service()
            self._indexing_service = service_factory.create_application_indexing_service()
            self._document_storage_management_service = service_factory.create_application_document_storage_management_service()
        except Exception as e:
            raise

    def _setup_global_logging(self, config: Config) -> None:
        """根据配置初始化 loguru 全局日志器"""
        # 清理默认处理器
        logger.remove()

        # 控制台处理器
        level = getattr(config.logging, 'level', 'INFO') or 'INFO'
        logger.add(
            sys.stdout,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )

        # 文件处理器（可选）
        file_path = getattr(config.logging, 'file_path', None)
        if isinstance(file_path, str) and file_path:
            rotation_mb = getattr(config.logging, 'max_file_size_mb', 10) or 10
            logger.add(
                file_path,
                level=level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                rotation=f"{rotation_mb} MB",
                retention="7 days",
                compression="zip"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康检查结果
        """
        try:
            health_status = {
                "overall": "healthy",
                "components": {}
            }
            
            # 检查嵌入服务
            try:
                test_embedding = await self.embedding_service.embed_text("测试")
                health_status["components"]["embedding_service"] = {
                    "status": "healthy",
                    "dimension": len(test_embedding)
                }
            except Exception as e:
                health_status["components"]["embedding_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall"] = "degraded"
            
            # 检查LLM服务
            try:
                test_response = await self.llm_service.generate_text("你好")
                health_status["components"]["llm_service"] = {
                    "status": "healthy",
                    "response_length": len(test_response)
                }
            except Exception as e:
                health_status["components"]["llm_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall"] = "degraded"
            
            # 检查向量存储服务
            try:
                doc_count = await self.vector_store_service.count()
                health_status["components"]["vector_store_service"] = {
                    "status": "healthy",
                    "document_count": doc_count
                }
            except Exception as e:
                health_status["components"]["vector_store_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall"] = "degraded"
            
            # 检查文档仓库
            try:
                docs = await self.document_repository.get_all_documents()
                health_status["components"]["document_repository"] = {
                    "status": "healthy",
                    "document_count": len(docs)
                }
            except Exception as e:
                health_status["components"]["document_repository"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall"] = "degraded"
            
            return {
                "success": True,
                "health_status": health_status
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"健康检查失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "health_status": {
                    "overall": "unhealthy",
                    "components": {}
                }
            }
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.logger:
                self.logger.info("开始清理应用容器资源...")
            
            # 保存向量存储索引
            if self._vector_store_service:
                await self._vector_store_service.save_index()
            
            # 清理其他资源
            # 这里可以添加其他需要清理的资源
            
            if self.logger:
                self.logger.info("应用容器资源清理完成")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"清理应用容器资源失败: {str(e)}")
    

# 全局容器实例
_container: Optional[ApplicationContainer] = None

def init_container(config: Optional[Config] = None,logger: Optional[LoggerService] = None) -> ApplicationContainer:
    """获取全局容器实例
    
    Args:
        config: 配置对象
        
    Returns:
        容器实例
    """
    global _container
    
    if _container is None:
        _container = ApplicationContainer(config,logger)
    
    return _container

def get_app_container() -> ApplicationContainer:
    """获取应用容器
    
    Returns:
        ApplicationContainer: 应用容器实例
        
    Raises:
        HTTPException: 如果容器未初始化
    """
    return _container