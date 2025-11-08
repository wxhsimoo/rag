from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMService(ABC):
    """大语言模型服务接口 - 定义文本生成的抽象方法"""
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本回复
        
        Args:
            prompt: 输入提示词
            **kwargs: 其他参数（如temperature, max_tokens等）
            
        Returns:
            生成的文本回复
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成
        
        Args:
            messages: 对话消息列表，格式为[{"role": "user/assistant/system", "content": "内容"}]
            **kwargs: 其他参数
            
        Returns:
            生成的回复
        """
        pass
    
    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs):
        """流式生成文本
        
        Args:
            prompt: 输入提示词
            **kwargs: 其他参数
            
        Yields:
            生成的文本片段
        """
        pass
    
    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """流式对话生成
        
        Args:
            messages: 对话消息列表
            **kwargs: 其他参数
            
        Yields:
            生成的回复片段
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
    def get_max_tokens(self) -> int:
        """获取最大token数
        
        Returns:
            最大token数
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
    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """验证消息格式
        
        Args:
            messages: 消息列表
            
        Returns:
            验证是否通过
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """计算文本的token数量
        
        Args:
            text: 要计算的文本
            
        Returns:
            token数量
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息
        
        Returns:
            服务信息字典
        """
        pass
    
    @abstractmethod
    def get_supported_parameters(self) -> List[str]:
        """获取支持的参数列表
        
        Returns:
            支持的参数名称列表
        """
        pass