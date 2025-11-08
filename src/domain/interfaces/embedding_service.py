from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class EmbeddingService(ABC):
    """嵌入服务接口 - 定义文本向量化的抽象方法"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """将单个文本转换为向量
        
        Args:
            text: 要向量化的文本
            
        Returns:
            文本的向量表示
        """
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量
        
        Args:
            texts: 要向量化的文本列表
            
        Returns:
            文本向量列表
        """
        pass
    
    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """将查询文本转换为向量
        
        Args:
            query: 查询文本
            
        Returns:
            查询向量
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """获取向量维度
        
        Returns:
            向量维度
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称
        
        Returns:
            模型名称
        """
        pass
    
    @abstractmethod
    def get_max_input_length(self) -> int:
        """获取最大输入长度
        
        Returns:
            最大输入长度
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """检查服务是否可用
        
        Returns:
            服务是否可用
        """
        pass
    
    @abstractmethod
    def validate_input(self, text: str) -> bool:
        """验证输入文本
        
        Args:
            text: 要验证的文本
            
        Returns:
            验证是否通过
        """
        pass
    
    @abstractmethod
    def preprocess_text(self, text: str) -> str:
        """预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息
        
        Returns:
            服务信息字典
        """
        pass