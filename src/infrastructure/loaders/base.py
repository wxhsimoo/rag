from abc import ABC, abstractmethod
from typing import List, Optional

from ...infrastructure.log.logger_service import LoggerService
from ..splitters.types import InfraDocument  # 复用基础设施层的文档类型
from .types import InfraLoaderConfig


class InfraDocumentLoader(ABC):
    """基础设施层的文档加载器抽象基类

    与领域层接口保持方法一致，但仅使用基础设施层的数据结构。
    """

    def __init__(self, config: Optional[InfraLoaderConfig] = None, logger: Optional[LoggerService] = None):
        self.config = config or InfraLoaderConfig()
        self.logger = logger

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """获取文件扩展名（不带点）"""
        return file_path.lower().split('.')[-1]

    @abstractmethod
    def supports_file_type(self, file_path: str) -> bool:
        """检查是否支持该文件类型"""
        raise NotImplementedError

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """返回支持的文件扩展名列表"""
        raise NotImplementedError

    @abstractmethod
    def load(self, file_path: str) -> List[InfraDocument]:
        """加载指定路径的文档，返回基础设施层文档列表"""
        raise NotImplementedError

