from typing import List, Dict, Any
import dashscope
from dashscope import Generation

from .base import LLMProvider
from ...infrastructure.config.config_manager import get_config

class AliyunQwenProvider(LLMProvider):
    """阿里云通义千问实现"""
    
    def __init__(self, api_key: str = None, model: str = None):
        config = get_config()
        self.api_key = api_key or config.ALIYUN_API_KEY
        self.model = model or config.ALIYUN_LLM_MODEL
        
        if not self.api_key:
            raise ValueError("阿里云API密钥未配置")
            
        dashscope.api_key = self.api_key
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本回复"""
        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1500),
                top_p=kwargs.get('top_p', 0.8)
            )
            
            if response.status_code == 200:
                print("-----------阿里云LLM API调用成功")
                return response.output.text
            else:
                raise Exception(f"阿里云LLM API调用失败: {response.message}")
                
        except Exception as e:
            raise Exception(f"阿里云LLM服务错误: {str(e)}")
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        try:
            response = Generation.call(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1500),
                top_p=kwargs.get('top_p', 0.8)
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"阿里云对话API调用失败: {response.message}")
                
        except Exception as e:
            raise Exception(f"阿里云对话服务错误: {str(e)}")
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model
    
    def get_max_tokens(self) -> int:
        """获取最大token数"""
        # 通义千问模型的最大token数
        if "qwen-turbo" in self.model:
            return 6000
        elif "qwen-plus" in self.model:
            return 30000
        elif "qwen-max" in self.model:
            return 6000
        else:
            return 6000  # 默认值
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        return await self.generate(prompt, **kwargs)
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成对话回复"""
        return await self.chat(messages, **kwargs)
    
    async def stream_generate(self, prompt: str, **kwargs):
        """流式生成文本"""
        # 阿里云暂不支持流式生成，返回普通生成结果
        result = await self.generate(prompt, **kwargs)
        yield result
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """流式对话生成"""
        # 阿里云暂不支持流式对话，返回普通对话结果
        result = await self.chat(messages, **kwargs)
        yield result
    
    async def generate_stream(self, prompt: str, **kwargs):
        """流式生成文本（兼容旧方法名）"""
        async for chunk in self.stream_generate(prompt, **kwargs):
            yield chunk
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.model,
            "provider": "aliyun",
            "max_tokens": self.get_max_tokens(),
            "supports_streaming": False
        }
    
    def get_max_input_length(self) -> int:
        """获取最大输入长度"""
        return self.get_max_tokens() - 1000  # 预留输出空间
    
    async def is_available(self) -> bool:
        """检查服务可用性"""
        try:
            await self.generate("test", max_tokens=10)
            return True
        except Exception:
            return False
    
    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """验证消息格式"""
        if not messages or not isinstance(messages, list):
            return False
        
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                return False
            if msg['role'] not in ['user', 'assistant', 'system']:
                return False
        
        return True
    
    def count_tokens(self, text: str) -> int:
        """估算token数量"""
        # 简单估算：中文按字符数，英文按单词数的1.3倍
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        other_chars = len(text) - chinese_chars
        return chinese_chars + int(other_chars * 0.25)
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "provider": "aliyun",
            "model": self.model,
            "max_tokens": self.get_max_tokens(),
            "max_input_length": self.get_max_input_length(),
            "supports_streaming": False,
            "api_key_configured": bool(self.api_key)
        }
    
    def get_supported_parameters(self) -> List[str]:
        """获取支持的参数列表"""
        return ["temperature", "max_tokens", "top_p"]