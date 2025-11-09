#!/usr/bin/env python3
"""
配置管理器

负责加载和管理系统配置，支持YAML配置文件和环境变量覆盖。
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1


@dataclass
class AppConfig:
    """应用配置"""
    name: str = "RAG系统"
    version: str = "1.0.0"
    # 移除 environment/debug/log_level，改为仅保留基础信息


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    file_path: str = ""
    max_file_size_mb: int = 100
    backup_count: int = 5


@dataclass
class OpenAIConfig:
    """OpenAI配置"""
    api_key: str = ""
    model: str = "gpt-3.5-turbo"
    api_base: str = "https://api.openai.com/v1"
    organization: Optional[str] = None


@dataclass
class EmbeddingConfig:
    """嵌入模型配置"""
    provider: str = "sentence_transformers"  # openai, aliyun, sentence_transformers
    batch_size: int = 32
    max_length: int = 512
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    aliyun: 'AliyunEmbeddingConfig' = field(default_factory=lambda: AliyunEmbeddingConfig())
    sentence_transformers: 'SentenceTransformersConfig' = field(default_factory=lambda: SentenceTransformersConfig())


@dataclass
class AliyunEmbeddingConfig:
    """阿里云嵌入模型配置"""
    api_key: str = ""
    model: str = "text-embedding-v1"
    api_base: str = "https://dashscope.aliyuncs.com/api/v1"


@dataclass
class AliyunLLMConfig:
    """阿里云LLM配置"""
    api_key: str = ""
    model: str = "qwen-turbo"
    api_base: str = "https://dashscope.aliyuncs.com/api/v1"


@dataclass
class SentenceTransformersConfig:
    """SentenceTransformers配置"""
    model: str = "all-MiniLM-L6-v2"
    device: str = "cpu"  # cpu, cuda


@dataclass
class LLMConfig:
    """大语言模型配置"""
    provider: str = "openai"  # openai, aliyun, anthropic
    max_tokens: int = 1000
    temperature: float = 0.7
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    aliyun: AliyunLLMConfig = field(default_factory=AliyunLLMConfig)
    

@dataclass
class AliyunConfig:
    """阿里云配置（兼容性保留）"""
    api_key: str = ""
    model: str = "qwen-turbo"
    api_base: str = "https://dashscope.aliyuncs.com/api/v1"


@dataclass
class AIProvidersConfig:
    """AI服务提供商配置"""
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    # 兼容性保留
    aliyun: AliyunConfig = field(default_factory=AliyunConfig)


@dataclass
class VectorStoreConfig:
    """向量存储配置"""
    provider: str = "faiss"
    type: str = "faiss"
    dimension: int = 384
    index_path: str = "./data/vector_index"


@dataclass
class DocumentRepositoryConfig:
    """文档仓储配置"""
    provider: str = "local_file"
    base_path: str = "./data"


@dataclass
class LocalDocumentsConfig:
    """本地文档存储配置"""
    base_path: str = "./data/storage"
    max_file_size_mb: int = 10
    documents_path: str = "./data"


@dataclass
class DocumentsConfig:
    """文档存储配置"""
    type: str = "local"
    local: LocalDocumentsConfig = field(default_factory=LocalDocumentsConfig)


@dataclass
class StorageConfig:
    """存储配置"""
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    documents: DocumentsConfig = field(default_factory=DocumentsConfig)
    document_repository: DocumentRepositoryConfig = field(default_factory=DocumentRepositoryConfig)


@dataclass
class RetrievalConfig:
    """检索配置"""
    top_k: int = 5
    similarity_threshold: float = 0.7
    max_context_length: int = 2000


@dataclass
class DocumentProcessingConfig:
    """文档处理配置"""
    chunk_size: int = 500
    chunk_overlap: int = 50
    supported_formats: list = field(default_factory=lambda: ["txt", "md", "json"])


@dataclass
class ConversationConfig:
    """对话配置"""
    max_history_length: int = 10
    session_timeout_minutes: int = 30


@dataclass
class RAGConfig:
    """RAG系统配置"""
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    document_processing: DocumentProcessingConfig = field(default_factory=DocumentProcessingConfig)
    conversation: ConversationConfig = field(default_factory=ConversationConfig)




@dataclass
class CORSConfig:
    """CORS配置"""
    allow_origins: list = field(default_factory=lambda: ["*"])
    allow_methods: list = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    allow_headers: list = field(default_factory=lambda: ["*"])

@dataclass
class Config:
    """主配置类"""
    app: AppConfig = field(default_factory=AppConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    ai_providers: AIProvidersConfig = field(default_factory=AIProvidersConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self._config: Optional[Config] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                self._config = self._create_config_from_dict(config_data or {})
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._config = Config()
            
            # 应用环境变量覆盖
            self._apply_env_overrides()
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.info("使用默认配置")
            self._config = Config()
    
    def _create_config_from_dict(self, data: Dict[str, Any]) -> Config:
        """从字典创建配置对象"""
        config = Config()
        
        # 应用配置
        if 'app' in data:
            app_data = data['app']
            config.app = AppConfig(
                name=app_data.get('name', config.app.name),
                version=app_data.get('version', config.app.version),
            )
        
        # 日志配置
        if 'logging' in data:
            logging_data = data['logging']
            config.logging = LoggingConfig(
                level=logging_data.get('level', config.logging.level),
                file_path=logging_data.get('file_path', config.logging.file_path),
                max_file_size_mb=logging_data.get('max_file_size_mb', config.logging.max_file_size_mb),
                backup_count=logging_data.get('backup_count', config.logging.backup_count),
            )
        
        # 服务器配置
        if 'server' in data:
            server_data = data['server']
            config.server = ServerConfig(
                host=server_data.get('host', config.server.host),
                port=server_data.get('port', config.server.port),
                reload=server_data.get('reload', config.server.reload),
                workers=server_data.get('workers', config.server.workers)
            )
        
        # AI服务配置
        if 'ai_providers' in data:
            ai_data = data['ai_providers']
            
            # 嵌入配置
            embedding_data = ai_data.get('embedding', {})
            openai_embedding = embedding_data.get('openai', {})
            aliyun_embedding = embedding_data.get('aliyun', {})
            sentence_transformers_embedding = embedding_data.get('sentence_transformers', {})
            
            config.ai_providers.embedding = EmbeddingConfig(
                provider=embedding_data.get('provider', config.ai_providers.embedding.provider),
                batch_size=embedding_data.get('batch_size', config.ai_providers.embedding.batch_size),
                max_length=embedding_data.get('max_length', config.ai_providers.embedding.max_length),
                openai=OpenAIConfig(
                    api_key=openai_embedding.get('api_key', ''),
                    model=openai_embedding.get('model', 'text-embedding-ada-002'),
                    api_base=openai_embedding.get('api_base', 'https://api.openai.com/v1'),
                    organization=openai_embedding.get('organization')
                ),
                aliyun=AliyunEmbeddingConfig(
                    api_key=aliyun_embedding.get('api_key', ''),
                    model=aliyun_embedding.get('model', 'text-embedding-v1'),
                    api_base=aliyun_embedding.get('api_base', 'https://dashscope.aliyuncs.com/api/v1')
                ),
                sentence_transformers=SentenceTransformersConfig(
                    model=sentence_transformers_embedding.get('model', 'all-MiniLM-L6-v2'),
                    device=sentence_transformers_embedding.get('device', 'cpu')
                )
            )
            
            # LLM配置
            llm_data = ai_data.get('llm', {})
            openai_llm = llm_data.get('openai', {})
            aliyun_llm = llm_data.get('aliyun', {})
            
            config.ai_providers.llm = LLMConfig(
                provider=llm_data.get('provider', config.ai_providers.llm.provider),
                max_tokens=llm_data.get('max_tokens', config.ai_providers.llm.max_tokens),
                temperature=llm_data.get('temperature', config.ai_providers.llm.temperature),
                openai=OpenAIConfig(
                    api_key=openai_llm.get('api_key', ''),
                    model=openai_llm.get('model', 'gpt-3.5-turbo'),
                    api_base=openai_llm.get('api_base', 'https://api.openai.com/v1'),
                    organization=openai_llm.get('organization')
                ),
                aliyun=AliyunLLMConfig(
                    api_key=aliyun_llm.get('api_key', ''),
                    model=aliyun_llm.get('model', 'qwen-turbo'),
                    api_base=aliyun_llm.get('api_base', 'https://dashscope.aliyuncs.com/api/v1')
                )
            )
        
        # 存储配置
        if 'storage' in data:
            storage_data = data['storage']
            vector_store_data = storage_data.get('vector_store', {})
            documents_data = storage_data.get('documents', {})
            local_documents_data = documents_data.get('local', {})
            
            # 处理向量存储配置
            faiss_data = vector_store_data.get('faiss', {})
            
            config.storage = StorageConfig(
                vector_store=VectorStoreConfig(
                    type=vector_store_data.get('type', config.storage.vector_store.type),
                    dimension=faiss_data.get('dimension', config.storage.vector_store.dimension),
                    index_path=faiss_data.get('index_path', config.storage.vector_store.index_path)
                ),
                documents=DocumentsConfig(
                    type=documents_data.get('type', config.storage.documents.type),
                    local=LocalDocumentsConfig(
                        base_path=local_documents_data.get('base_path', config.storage.documents.local.base_path),
                        max_file_size_mb=local_documents_data.get('max_file_size_mb', config.storage.documents.local.max_file_size_mb),
                        documents_path=local_documents_data.get('documents_path', config.storage.documents.local.documents_path)
                    )
                )
            )
        
        # RAG配置
        if 'rag' in data:
            rag_data = data['rag']
            retrieval_data = rag_data.get('retrieval', {})
            doc_processing_data = rag_data.get('document_processing', {})
            conversation_data = rag_data.get('conversation', {})
            
            config.rag = RAGConfig(
                retrieval=RetrievalConfig(
                    top_k=retrieval_data.get('top_k', config.rag.retrieval.top_k),
                    similarity_threshold=retrieval_data.get('similarity_threshold', config.rag.retrieval.similarity_threshold),
                    max_context_length=retrieval_data.get('max_context_length', config.rag.retrieval.max_context_length)
                ),
                document_processing=DocumentProcessingConfig(
                    chunk_size=doc_processing_data.get('chunk_size', config.rag.document_processing.chunk_size),
                    chunk_overlap=doc_processing_data.get('chunk_overlap', config.rag.document_processing.chunk_overlap),
                    supported_formats=doc_processing_data.get('supported_formats', config.rag.document_processing.supported_formats)
                ),
                conversation=ConversationConfig(
                    max_history_length=conversation_data.get('max_history_length', config.rag.conversation.max_history_length),
                    session_timeout_minutes=conversation_data.get('session_timeout_minutes', config.rag.conversation.session_timeout_minutes)
                )
            )
        
        return config
    
    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        if not self._config:
            return
        
        # 应用环境：已移除对 app.environment 的覆盖
        
        # 服务器配置
        env_val = os.getenv('HOST')
        if env_val:
            self._config.server.host = env_val
        env_val = os.getenv('PORT')
        if env_val:
            try:
                self._config.server.port = int(env_val)
            except ValueError:
                logger.warning(f"无效的端口号: {env_val}")
        
        # OpenAI API密钥
        env_val = os.getenv('OPENAI_API_KEY')
        if env_val:
            self._config.ai_providers.embedding.openai.api_key = env_val
            self._config.ai_providers.llm.openai.api_key = env_val
        
        # 日志级别
        env_val = os.getenv('LOG_LEVEL')
        if env_val:
            # 仅更新日志配置
            self._config.logging.level = env_val

        # 日志文件路径
        env_val = os.getenv('LOG_FILE_PATH')
        if env_val:
            self._config.logging.file_path = env_val

        # 日志文件最大尺寸（MB）
        env_val = os.getenv('LOG_MAX_FILE_SIZE_MB')
        if env_val:
            try:
                self._config.logging.max_file_size_mb = int(env_val)
            except ValueError:
                logger.warning(f"无效的日志最大文件大小: {env_val}")

        # 日志备份文件数量
        env_val = os.getenv('LOG_BACKUP_COUNT')
        if env_val:
            try:
                self._config.logging.backup_count = int(env_val)
            except ValueError:
                logger.warning(f"无效的日志备份数量: {env_val}")
    
    def get_config(self) -> Config:
        """获取配置对象"""
        if self._config is None:
            self._load_config()
        return self._config
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            config = self.get_config()
            
            # 验证必要的配置项
            if not config.storage.documents.local.documents_path:
                logger.error("文档路径未配置")
                return False
            
            if config.ai_providers.llm.provider == "openai":
                if not config.ai_providers.llm.openai.api_key:
                    logger.warning("OpenAI API密钥未配置")
            
            # 验证路径存在性
            docs_path = Path(config.storage.documents.local.documents_path)
            if not docs_path.exists():
                logger.info(f"创建文档目录: {docs_path}")
                docs_path.mkdir(parents=True, exist_ok=True)
                
            # 验证存储基础路径
            base_path = Path(config.storage.documents.local.base_path)
            if not base_path.exists():
                logger.info(f"创建存储目录: {base_path}")
                base_path.mkdir(parents=True, exist_ok=True)
            
            index_path = Path(config.storage.vector_store.index_path)
            if not index_path.parent.exists():
                logger.info(f"创建索引目录: {index_path.parent}")
                index_path.parent.mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def get_env_info(self) -> Dict[str, Any]:
        """获取环境信息"""
        config = self.get_config()
        return {
            "version": config.app.version,
            "log_level": config.logging.level,
            "python_version": os.sys.version,
            "config_path": str(self.config_path),
            "config_exists": self.config_path.exists()
        }


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: str = "config.yaml") -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        # 支持通过环境变量覆盖配置路径
        env_path = os.getenv("CONFIG_PATH") or config_path
        _config_manager = ConfigManager(env_path)
    return _config_manager


def get_config() -> Config:
    """获取配置对象的便捷函数"""
    return get_config_manager().get_config()