from typing import List, Dict, Any
from openai import OpenAI

from .base import LLMProvider
from ...infrastructure.config.config_manager import get_config

class OpenAIChatGPTProvider(LLMProvider):
    """OpenAI ChatGPT实现"""
    
    def __init__(self, api_key: str = None, model: str = None):
        config = get_config()
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_LLM_MODEL
        
        if not self.api_key:
            raise ValueError("OpenAI API密钥未配置")
            
        self.client = OpenAI(api_key=self.api_key)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本回复"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1500),
                top_p=kwargs.get('top_p', 1.0)
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            raise Exception(f"OpenAI LLM服务错误: {str(e)}")
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1500),
                top_p=kwargs.get('top_p', 1.0)
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            raise Exception(f"OpenAI对话服务错误: {str(e)}")
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model
    
    def get_max_tokens(self) -> int:
        """获取最大token数"""
        # OpenAI模型的最大token数
        if "gpt-3.5-turbo" in self.model:
            return 4096
        elif "gpt-4" in self.model:
            if "32k" in self.model:
                return 32768
            else:
                return 8192
        elif "gpt-4-turbo" in self.model:
            return 128000
        else:
            return 4096  # 默认值
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        return await self.generate(prompt, **kwargs)
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成对话回复"""
        return await self.chat(messages, **kwargs)
    
    async def generate_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1500),
                top_p=kwargs.get('top_p', 1.0),
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise Exception(f"OpenAI流式生成错误: {str(e)}")
    
    async def stream_generate(self, prompt: str, **kwargs):
        """流式生成文本 - Domain层接口"""
        async for chunk in self.generate_stream(prompt, **kwargs):
            yield chunk
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """流式对话生成 - Domain层接口"""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1500),
                top_p=kwargs.get('top_p', 1.0),
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise Exception(f"OpenAI流式对话错误: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.model,
            "provider": "openai",
            "max_tokens": self.get_max_tokens(),
            "supports_streaming": True
        }
    
    def get_max_input_length(self) -> int:
        """获取最大输入长度"""
        return self.get_max_tokens() - 1000  # 预留输出空间
    
    async def is_available(self) -> bool:
        """检查服务可用性"""
        try:
            # 简单测试API连接
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except:
            return False
    
    async def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """验证消息格式"""
        if not messages or not isinstance(messages, list):
            return False
        
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                return False
            if msg['role'] not in ['user', 'assistant', 'system']:
                return False
        
        return True
    
    async def count_tokens(self, text: str) -> int:
        """估算token数量"""
        # 简单估算：英文按单词数的1.3倍，中文按字符数
        words = len(text.split())
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        return int(words * 1.3) + chinese_chars
    
    async def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "provider": "openai",
            "model": self.model,
            "max_tokens": self.get_max_tokens(),
            "max_input_length": self.get_max_input_length(),
            "supports_streaming": True,
            "api_key_configured": bool(self.api_key)
        }
    
    async def get_supported_parameters(self) -> List[str]:
        """获取支持的参数"""
        return ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]