from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Optional
from ...domain.interfaces import EmbeddingService

class EmbeddingProvider(EmbeddingService):
    """向量嵌入提供者接口"""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """将文本转换为向量嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            向量嵌入列表
        """
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量嵌入
        
        Args:
            texts: 输入文本列表
            
        Returns:
            向量嵌入列表的列表
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """获取向量维度
        
        Returns:
            向量维度
        """
        pass
    
    # Domain层接口实现
    async def embed_query(self, query: str) -> List[float]:
        """查询向量化 - Domain层接口"""
        return await self.embed(query)
    
    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称 - Domain层接口"""
        pass
    
    @abstractmethod
    def get_max_input_length(self) -> int:
        """获取最大输入长度 - Domain层接口"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """检查服务可用性 - Domain层接口"""
        pass
    
    async def validate_input(self, text: str) -> bool:
        """验证输入 - Domain层接口"""
        if not text or not text.strip():
            return False
        if len(text) > self.get_max_input_length():
            return False
        return True
    
    async def preprocess_text(self, text: str) -> str:
        """文本预处理 - Domain层接口"""
        # 基本的文本清理
        return text.strip()
    
    async def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息 - Domain层接口"""
        return {
            "model_name": self.get_model_name(),
            "dimension": self.get_dimension(),
            "max_input_length": self.get_max_input_length(),
            "available": await self.is_available()
        }