import logging
from typing import Any, Optional
from .logger_service import LoggerService


class LoggerServiceImpl(LoggerService):
    """日志服务实现类"""
    
    def __init__(self, name: str, level: str = "INFO"):
        """初始化日志服务
        
        Args:
            name: 日志器名称
            level: 日志级别
        """
        self._name = name
        self._logger = logging.getLogger(name)
        self.set_level(level)
        
        # 如果没有处理器，添加默认的控制台处理器
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录调试信息"""
        self._logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录一般信息"""
        self._logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录警告信息"""
        self._logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录错误信息"""
        self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录严重错误信息"""
        self._logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录异常信息（包含堆栈跟踪）"""
        self._logger.exception(message, *args, **kwargs)
    
    def set_level(self, level: str) -> None:
        """设置日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        log_level = level_map.get(level.upper(), logging.INFO)
        self._logger.setLevel(log_level)
    
    def get_logger_name(self) -> str:
        """获取日志器名称"""
        return self._name