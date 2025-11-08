from typing import List, Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings

from .base import EmbeddingProvider

class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """HuggingFace嵌入模型实现 - 基于LangChain"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cuda' if self._is_cuda_available() else 'cpu'}
        )
    
    def _is_cuda_available(self) -> bool:
        """检查CUDA是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    async def embed(self, text: str) -> List[float]:
        """将文本转换为向量嵌入"""
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            raise Exception(f"HuggingFace嵌入服务错误: {str(e)}")
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量嵌入"""
        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            raise Exception(f"HuggingFace批量嵌入服务错误: {str(e)}")
    
    async def embed_text(self, text: str) -> List[float]:
        """将文本转换为向量嵌入 - Domain接口实现"""
        return await self.embed(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量嵌入 - Domain接口实现"""
        return await self.embed_batch(texts)
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        # 根据模型名称返回对应的维度
        if "all-MiniLM-L6-v2" in self.model_name:
            return 384
        elif "all-mpnet-base-v2" in self.model_name:
            return 768
        else:
            # 使用langchain获取维度
            try:
                test_embedding = self.embeddings.embed_query("test")
                return len(test_embedding)
            except Exception:
                return 384  # 默认维度
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name
    
    def get_max_input_length(self) -> int:
        """获取最大输入长度"""
        return 512  # HuggingFace模型的典型最大输入长度
    
    async def is_available(self) -> bool:
        """检查服务可用性"""
        try:
            # 测试一个简单的嵌入请求
            await self.embed_text("test")
            return True
        except Exception:
            return False
    
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
            "provider": "huggingface",
            "model": self.model_name,
            "dimension": self.get_dimension(),
            "max_input_length": self.get_max_input_length(),
            "cuda_available": self._is_cuda_available()
        }