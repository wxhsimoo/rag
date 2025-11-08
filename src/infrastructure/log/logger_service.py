from abc import ABC, abstractmethod
from typing import Any, Optional


class LoggerService(ABC):
    """日志服务接口"""
    
    @abstractmethod
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录调试信息"""
        pass
    
    @abstractmethod
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录一般信息"""
        pass
    
    @abstractmethod
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录警告信息"""
        pass
    
    @abstractmethod
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录错误信息"""
        pass
    
    @abstractmethod
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录严重错误信息"""
        pass
    
    @abstractmethod
    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录异常信息（包含堆栈跟踪）"""
        pass
    
    @abstractmethod
    def set_level(self, level: str) -> None:
        """设置日志级别"""
        pass
    
    @abstractmethod
    def get_logger_name(self) -> str:
        """获取日志器名称"""
        pass