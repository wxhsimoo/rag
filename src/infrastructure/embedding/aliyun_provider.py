from typing import List, Dict, Any
from langchain_community.embeddings import DashScopeEmbeddings

from .base import EmbeddingProvider
from ...infrastructure.config.config_manager import get_config

class AliyunEmbeddingProvider(EmbeddingProvider):
    """阿里云通用文本向量模型实现 - 基于LangChain"""
    
    def __init__(self, api_key: str = None, model: str = None):
        config = get_config()
        self.api_key = api_key or config.ai_providers.embedding.aliyun.api_key
        self.model = model or config.ai_providers.embedding.aliyun.model
        
        if not self.api_key:
            raise ValueError("阿里云API密钥未配置")
            
        self.embeddings = DashScopeEmbeddings(
            dashscope_api_key=self.api_key,
            model=self.model
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """将文本转换为向量嵌入"""
        try:
            return await self.embeddings.aembed_query(text)
        except Exception as e:
            raise Exception(f"阿里云嵌入服务错误: {str(e)}")
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量嵌入"""
        try:
            return await self.embeddings.aembed_documents(texts)
        except Exception as e:
            raise Exception(f"阿里云批量嵌入服务错误: {str(e)}")
    
    async def embed(self, text: str) -> List[float]:
        """兼容性方法 - 将文本转换为向量嵌入"""
        return await self.embed_text(text)
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """兼容性方法 - 批量将文本转换为向量嵌入"""
        return await self.embed_texts(texts)
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        # 阿里云text-embedding-v1模型的向量维度是1536
        return 1536
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model
    
    def get_max_input_length(self) -> int:
        """获取最大输入长度"""
        return 8192  # 阿里云嵌入模型的最大输入长度
    
    async def is_available(self) -> bool:
        """检查服务可用性"""
        try:
            # 测试一个简单的嵌入请求
            await self.embed_text("test")
            return True
        except Exception:
            return False
    
    async def embed_query(self, query: str) -> List[float]:
        """为查询文本生成嵌入向量"""
        return await self.embed(query)
    
    def validate_input(self, text: str) -> bool:
        """验证输入文本"""
        if not text or not isinstance(text, str):
            return False
        return len(text.strip()) <= self.get_max_input_length()
    
    def preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 基本的文本清理
        text = text.strip()
        # 截断过长的文本
        max_length = self.get_max_input_length()
        if len(text) > max_length:
            text = text[:max_length]
        return text
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "provider": "aliyun",
            "model": self.model,
            "dimension": self.get_dimension(),
            "max_input_length": self.get_max_input_length(),
            "api_key_configured": bool(self.api_key)
        }