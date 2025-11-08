from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class InfraLoaderConfig:
    """基础设施层的文档加载器配置

    统一承载各加载器需要的参数，避免直接依赖领域层类型。
    """
    encoding: str = "utf-8"
    split_by_headers: bool = True
    chunk_size: Optional[int] = None
    custom_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}

