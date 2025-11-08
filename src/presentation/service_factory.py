"""统一服务工厂类 - DDD架构实现

按照DDD分层架构原则：
1. 先初始化Infrastructure层（基础设施层）
2. 再初始化Domain层（领域层）
3. 最后初始化Application层（应用层）

调用链：Application -> Domain -> Infrastructure
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from ..infrastructure.config.config_manager import Config

# Application层实现导入
from ..application.services.indexing_service import IndexingService
from ..application.services.rag_pipeline_service import RAGPipelineService
from ..application.services.document_storage_management_service import DocumentStorageManagementService


# Domain层接口导入
from ..domain.interfaces.embedding_service import EmbeddingService
from ..domain.interfaces.llm_service import LLMService
from ..domain.interfaces.vector_store_service import VectorStoreService
from ..domain.interfaces.document_storage_service import DocumentStorageService
from ..domain.interfaces.document_loader_service import DocumentLoaderService
from ..domain.interfaces.document_splitter_service import DocumentSplitterService
from ..domain.interfaces.prompt_service import PromptService, PromptServiceAdapter


# Infrastructure层实现导入
from ..infrastructure.embedding.openai_provider import OpenAIEmbeddingProvider
from ..infrastructure.embedding.aliyun_provider import AliyunEmbeddingProvider
from ..infrastructure.llm.openai_provider import OpenAIChatGPTProvider
from ..infrastructure.llm.aliyun_provider import AliyunQwenProvider
from ..infrastructure.vector_store.faiss_store import FAISSVectorStore
from ..domain.services.prompt_service_impl import PromptServiceImpl as DomainPromptServiceImpl
from ..infrastructure.document_storage.local_provider import LocalDocumentStorageProvider
from ..infrastructure.splitters.document_splitter_service_impl import DocumentSplitterServiceImpl
from ..infrastructure.loaders.document_loader_service_impl import DocumentLoaderServiceImpl
from ..infrastructure.log.logger_service import LoggerService
from ..infrastructure.log.logger_service_impl import LoggerServiceImpl
from ..infrastructure.document_storage.s3_provider import S3DocumentStorageProvider



class DDDServiceFactory:
    """DDD架构统一服务工厂类
    
    实现分层初始化：Infrastructure -> Domain -> Application
    """
    _GLOBAL_EMBEDDING_SERVICE: EmbeddingService
    _GLOBAL_VECTOR_STORE_SERVICE: VectorStoreService 
    _GLOBAL_DOCUMENT_STORAGE_SERVICE: DocumentStorageService 
    _GLOBAL_DOCUMENT_SPLITTER_SERVICE: DocumentSplitterService 
    _GLOBAL_DOCUMENT_LOADER_SERVICE: DocumentLoaderService 
    _GLOBAL_PROMPT_SERVICE: Any

    def __init__(self, config: Optional[Config] = None):
        self.config = config
        
        # Infrastructure层提供器注册表
        self._embedding_providers: Dict[str, type] = {}
        self._llm_providers: Dict[str, type] = {}
        self._vector_store_providers: Dict[str, type] = {}
        self._document_storage_providers: Dict[str, type] = {}
        
        # 创建日志服务实例
        self._logger_service = LoggerServiceImpl("DDDServiceFactory")
        
        # 注册Infrastructure层默认提供器
        self._register_infrastructure_providers()

        # 初始化domian
        self._init_domain_service()

    def _init_domain_service(self):
        """初始化Domain层服务"""
         # ==================== 模块级全局服务实例缓存 ====================
        # 通过缓存避免重复创建，供应用层直接引用
        self._GLOBAL_EMBEDDING_SERVICE = self.create_domain_embedding_service()
        self._GLOBAL_LLM_SERVICE = self.create_domain_llm_service()
        # 先保证嵌入服务已就绪，再创建向量存储
        self._GLOBAL_VECTOR_STORE_SERVICE = self.create_domain_vector_store_service(self._GLOBAL_EMBEDDING_SERVICE)
        self._GLOBAL_DOCUMENT_SPLITTER_SERVICE = self.create_domain_document_splitter_service()
        self._GLOBAL_DOCUMENT_LOADER_SERVICE = self.create_domain_document_loader_service()
        self._GLOBAL_DOCUMENT_STORAGE_SERVICE = self.create_domain_document_storage_service()
        self._GLOBAL_PROMPT_SERVICE = self.create_domain_prompt_service()
   
    def _register_infrastructure_providers(self):
        """注册Infrastructure层服务提供器"""
        # 注册嵌入服务提供器
        self._embedding_providers['openai'] = OpenAIEmbeddingProvider
        self._embedding_providers['aliyun'] = AliyunEmbeddingProvider
        
        # 注册LLM服务提供器
        self._llm_providers['openai'] = OpenAIChatGPTProvider
        self._llm_providers['aliyun'] = AliyunQwenProvider
        
        # 注册向量存储提供器
        self._vector_store_providers['faiss'] = FAISSVectorStore
        
        # 注册文档仓储提供器
        self._document_storage_providers['local'] = LocalDocumentStorageProvider
        self._document_storage_providers['s3'] = S3DocumentStorageProvider
    
    # ==================== Infrastructure层服务创建 ====================
    
    def create_infrastructure_embedding_service(self, ) -> EmbeddingService:
        """创建Infrastructure层嵌入服务"""
        provider_name = self.config.ai_providers.embedding.provider
        
        if provider_name not in self._embedding_providers:
            raise ValueError(f"未知的嵌入服务提供器: {provider_name}")
        
        provider_class = self._embedding_providers[provider_name]
        
        # 根据提供器类型传递不同的配置参数
        if provider_name == 'openai':
            return provider_class(
                api_key=self.config.ai_providers.embedding.openai.api_key,
                model=self.config.ai_providers.embedding.openai.model
            )
        elif provider_name == 'aliyun':
            return provider_class(
                api_key=self.config.ai_providers.embedding.aliyun.api_key,
                model=self.config.ai_providers.embedding.aliyun.model
            )
        else:
            return provider_class()
    
    def create_infrastructure_llm_service(self) -> LLMService:
        """创建Infrastructure层LLM服务"""
        provider_name = self.config.ai_providers.llm.provider
        
        if provider_name not in self._llm_providers:
            raise ValueError(f"未知的LLM服务提供器: {provider_name}")
        
        provider_class = self._llm_providers[provider_name]
        
        # 根据提供器类型传递不同的配置参数
        if provider_name == 'openai':
            return provider_class(
                api_key=self.config.ai_providers.llm.openai.api_key,
                model=self.config.ai_providers.llm.openai.model
            )
        elif provider_name == 'aliyun':
            return provider_class(
                api_key=self.config.ai_providers.llm.aliyun.api_key,
                model=self.config.ai_providers.llm.aliyun.model
            )
        else:
            return provider_class()
    
    def create_infrastructure_vector_store_service(self, embedding_service: Optional[EmbeddingService] = None) -> VectorStoreService:
        """创建Infrastructure层向量存储服务"""
        provider_name = self.config.storage.vector_store.provider
        
        if provider_name not in self._vector_store_providers:
            raise ValueError(f"未知的向量存储服务提供器: {provider_name}")
        
        provider_class = self._vector_store_providers[provider_name]
        
        # 根据提供器类型传递不同的配置参数
        if provider_name == 'faiss':
            return provider_class(
                dimension=self.config.storage.vector_store.dimension,
                index_path=self.config.storage.vector_store.index_path,
                embedding_service=embedding_service
            )
        else:
            return provider_class()
    
    def create_infrastructure_document_storage_service(self) -> DocumentStorageService:
        """创建Infrastructure层文档仓储"""
        provider_name = self.config.storage.documents.type
        
        if provider_name not in self._document_storage_providers:
            raise ValueError(f"未知的文档仓储提供器: {provider_name}")
        
        provider_class = self._document_storage_providers[provider_name]
        
        # 根据提供器类型传递不同的配置参数
        if provider_name == 'local':
            logger = self.create_logger_service("LocalDocumentStorageProvider")
            return provider_class(
                data_path=self.config.storage.documents.local.base_path,
                logger=logger,
            )
        elif provider_name == 's3':
            logger = self.create_logger_service("S3DocumentStorageProvider")
            return provider_class(
                bucket_name=self.config.storage.documents.s3.bucket_name,
                endpoint_url=self.config.storage.documents.s3.endpoint_url,
                access_key=self.config.storage.documents.s3.access_key,
                secret_key=self.config.storage.documents.s3.secret_key,
                region_name=self.config.storage.documents.s3.region_name,
                use_ssl=self.config.storage.documents.s3.use_ssl,
                base_prefix=self.config.storage.documents.s3.base_prefix,
                logger=logger,
            )
        else:
            return provider_class()
    
    def create_infrastructure_document_splitter_service(self) -> DocumentSplitterService:
        """创建Infrastructure层文档分割服务"""
        logger = self.create_logger_service("DocumentSplitterService")
        return DocumentSplitterServiceImpl(logger=logger)
    
    def create_infrastructure_document_loader_service(self) -> DocumentLoaderService:
        """创建Infrastructure层文档加载服务"""
        logger = self.create_logger_service("DocumentLoaderService")
        return DocumentLoaderServiceImpl(logger)
    
    def create_logger_service(self, name: str) -> LoggerService:
        """创建日志服务"""
        return LoggerServiceImpl(name)

    def create_infrastructure_prompt_service(self) -> PromptService:
        """创建Infrastructure层提示词服务（保留占位，当前不直接使用）"""
        # 提示：按照当前约定，Prompt 的具体构建在基础设施层实现为构建器，
        # 由 Domain 层的 PromptService 进行调用与类型转换。
        # 因此这里不直接返回实现，保留占位以便未来扩展。
        return DomainPromptServiceImpl()
    
    # ==================== Domain层服务创建（基于Infrastructure层） ====================
    def create_domain_embedding_service(self) -> EmbeddingService:
        """创建Domain层嵌入服务（委托给Infrastructure层）"""
        instance = self.create_infrastructure_embedding_service()
        self._GLOBAL_EMBEDDING_SERVICE = instance
        return instance
    
    def create_domain_llm_service(self) -> LLMService:
        """创建Domain层LLM服务（委托给Infrastructure层）"""
        instance = self.create_infrastructure_llm_service()
        self._GLOBAL_LLM_SERVICE = instance
        return instance
    
    def create_domain_vector_store_service(self, embedding_service: Optional[EmbeddingService] = None) -> VectorStoreService:
        """创建Domain层向量存储服务（委托给Infrastructure层）"""
        emb = embedding_service or self._GLOBAL_EMBEDDING_SERVICE or self.create_domain_embedding_service()
        instance = self.create_infrastructure_vector_store_service(emb)
        self._GLOBAL_VECTOR_STORE_SERVICE = instance
        return instance
    
    def create_domain_document_storage_service(self) -> DocumentStorageService:
        """创建Domain层文档仓储（委托给Infrastructure层）"""
        instance = self.create_infrastructure_document_storage_service()
        self._GLOBAL_DOCUMENT_STORAGE_SERVICE = instance
        return instance

    
    def create_domain_document_splitter_service(self) -> DocumentSplitterService:
        """创建Domain层文档分割服务（委托给Infrastructure层）"""
        instance = self.create_infrastructure_document_splitter_service()
        self._GLOBAL_DOCUMENT_SPLITTER_SERVICE = instance
        return instance
    
    def create_domain_document_loader_service(self) -> DocumentLoaderService:
        """创建Domain层文档加载服务（委托给Infrastructure层）"""
        instance = self.create_infrastructure_document_loader_service()
        self._GLOBAL_DOCUMENT_LOADER_SERVICE = instance
        return instance

    def create_domain_prompt_service(self) -> PromptService:
        """创建Domain层提示词服务（使用适配器包装 ctx 接口，实现旧签名调用）"""
        impl = DomainPromptServiceImpl()
        instance = PromptServiceAdapter(impl)
        self._GLOBAL_PROMPT_SERVICE = instance
        return instance
    
    # ==================== Application层服务创建（基于Domain层） ====================
    def create_application_rag_pipeline_service(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store_service: Optional[VectorStoreService] = None,
        llm_service: Optional[LLMService] = None
    ) -> RAGPipelineService:
        """创建Application层RAG管道服务"""
        # 如果没有提供依赖，则从Domain层创建
        embedding_service = self._GLOBAL_EMBEDDING_SERVICE 
        vector_store_service = self._GLOBAL_VECTOR_STORE_SERVICE
        llm_service =  self._GLOBAL_LLM_SERVICE
        prompt_service = self._GLOBAL_PROMPT_SERVICE
        
        # 创建日志服务
        logger = self.create_logger_service("RAGPipelineService")
        
        return RAGPipelineService(
            embedding_service=embedding_service,
            vector_store_service=vector_store_service,
            llm_service=llm_service,
            logger=logger,
            prompt_service=prompt_service,
        )
    
    def create_application_document_storage_management_service(
        self,
        document_storage_service: Optional[DocumentStorageService] = None,
    ) -> DocumentStorageManagementService:
        """创建Application层文件管理服务"""
        # 如果没有提供依赖，则从Domain层创建
        document_storage_service = self._GLOBAL_DOCUMENT_STORAGE_SERVICE
        
        # 创建日志服务
        logger = self.create_logger_service("DocumentStorageManagementService")
        
        return DocumentStorageManagementService(
            repo=document_storage_service,
            logger=logger
        )

    def create_application_indexing_service(
        self,
        document_loader_service: Optional[DocumentLoaderService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store_service: Optional[VectorStoreService] = None,
        document_splitter_service: Optional[DocumentSplitterService] = None
    ) -> IndexingService:
        """创建Application层索引服务"""
        document_loader_service = self._GLOBAL_DOCUMENT_LOADER_SERVICE
        embedding_service = self._GLOBAL_EMBEDDING_SERVICE
        vector_store_service = self._GLOBAL_VECTOR_STORE_SERVICE
        document_splitter_service = self._GLOBAL_DOCUMENT_SPLITTER_SERVICE
       
        # 创建日志服务
        logger = self.create_logger_service("IndexingService")
        
        return IndexingService(
            document_loader_service=document_loader_service,
            embedding_service=embedding_service,
            vector_store_service=vector_store_service,
            document_splitter_service=document_splitter_service,
            logger=logger
        )
    
