import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, Optional
from .logger_service import LoggerService
from ..config.config_manager import get_config


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

        # 读取配置
        try:
            cfg = get_config()
            log_cfg = getattr(cfg, "logging", None)
        except Exception:
            cfg = None
            log_cfg = None

        # 设置日志级别（优先使用配置）
        effective_level = level
        if log_cfg and isinstance(log_cfg.level, str) and log_cfg.level:
            effective_level = log_cfg.level
        self.set_level(effective_level)
        
        # 如果没有处理器，添加默认的控制台处理器
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

        # 按配置添加文件处理器（带大小轮转）
        if log_cfg and isinstance(log_cfg.file_path, str) and log_cfg.file_path:
            file_path = log_cfg.file_path
            max_bytes = int(log_cfg.max_file_size_mb) * 1024 * 1024
            backup_count = int(log_cfg.backup_count)

            # 确保目录存在；如文件不存在则创建
            try:
                os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
                if not os.path.exists(file_path):
                    open(file_path, 'a', encoding='utf-8').close()
            except Exception:
                # 目录或文件创建失败时，保持仅控制台日志
                pass

            # 避免重复添加同路径的文件处理器
            existing_file_handlers = [h for h in self._logger.handlers 
                                       if isinstance(h, RotatingFileHandler) and getattr(h, 'baseFilename', None) == file_path]
            if not existing_file_handlers:
                file_handler = RotatingFileHandler(
                    file_path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
                self._logger.addHandler(file_handler)
    
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