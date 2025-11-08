from typing import List, Optional

from ..interfaces.prompt_service import PromptService
from ...infrastructure.prompt.types import PromptContext
from ...infrastructure.prompt.prompt_service_impl import PromptBuilderImpl


class PromptServiceImpl(PromptService):
    """Domain 层的 PromptService 实现。

    负责将 PromptContext 委托至基础设施层构建器生成提示词字符串。
    """

    def __init__(self) -> None:
        self._builder = PromptBuilderImpl()

    async def build_prompt(self, ctx: PromptContext) -> str:
        return await self._builder.build_prompt(ctx)
