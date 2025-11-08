from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from ...domain.interfaces import LLMService

class LLMProvider(LLMService):
    """大语言模型提供者接口"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
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
    
    # Domain层接口实现
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本 - Domain层接口"""
        return await self.generate(prompt, **kwargs)
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成 - Domain层接口"""
        return await self.chat(messages, **kwargs)
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成 - Domain层接口"""
        pass
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息 - Domain层接口"""
        return {
            "model_name": self.get_model_name(),
            "max_tokens": self.get_max_tokens(),
            "max_input_length": self.get_max_input_length()
        }
    
    @abstractmethod
    def get_max_input_length(self) -> int:
        """获取最大输入长度 - Domain层接口"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """检查服务可用性 - Domain层接口"""
        pass
    
    async def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """验证消息格式 - Domain层接口"""
        if not messages:
            return False
        
        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in ["user", "assistant", "system"]:
                return False
            if not msg["content"] or not msg["content"].strip():
                return False
        
        return True
    
    async def count_tokens(self, text: str) -> int:
        """计算token数量 - Domain层接口"""
        # 简单估算，实际实现应该使用具体模型的tokenizer
        return len(text.split())
    
    async def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息 - Domain层接口"""
        return {
            "model_name": self.get_model_name(),
            "max_tokens": self.get_max_tokens(),
            "max_input_length": self.get_max_input_length(),
            "available": await self.is_available()
        }
    
    async def get_supported_parameters(self) -> List[str]:
        """获取支持的参数 - Domain层接口"""
        return ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]