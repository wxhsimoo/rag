from typing import List, Optional

from .types import PromptContext, PromptDoc


class PromptBuilderImpl:
    """基础设施层 Prompt 构建器实现（不依赖 domain）。
    
    入参为本层自定义的 PromptContext，仿照 LangChain 的风格组装提示，
    并强制统一 JSON 输出模式（structured_v1）。
    """

    async def build_prompt(self, ctx: PromptContext) -> str:
        parts: List[str] = []

        # 系统角色
        parts.append(
            "你是一个专业的文档问答助手。"
            "请严格基于参考资料回答问题，不要引用其他来源。"
        )

        # 对话历史
        if ctx.history_lines:
            parts.append("\n对话历史:")
            parts.append("\n".join(ctx.history_lines))

        # 参考资料
        if ctx.docs:
            parts.append("\n参考资料:")
            for i, doc in enumerate(ctx.docs, 1):
                source_info = f" (来源: {doc.source})" if doc.source else ""
                parts.append(f"{i}. {doc.content}{source_info}")

        # 用户问题
        parts.append(f"\n用户问题: {ctx.question}")

        # 回答要求
        parts.append(
            "\n回答要求:\n"
            "1. 仅依据参考资料，不要编造信息\n"
            "2. 结构清晰、简洁，必要时用要点列举\n"
            "3. 如引用，请附上来源或段落编号\n"
            "4. 若资料不足，请说明不足并给出建议的下一步"
        )

        # 固定输出格式（严格遵守）
        parts.append(
            "\n输出格式（必须严格遵守）:\n"
            "- 仅输出一个 JSON 对象，不要使用代码块或附加解释。\n"
            "- 字段如下：\n"
            "  {\"format\":\"structured_v1\",\n"
            "   \"summary\": string,\n"
            "   \"key_points\": [string,...],  // 仅答案要点，不含来源/引用\n"
            "   \"citations\": [{\"source\": string, \"snippet\": string}, ...]\n"
            "  }\n"
            "- 不要输出示例或提示语，仅返回 JSON。\n"
            "- 若资料不足，\"summary\"需明确说明，\"key_points\"可为空，\"citations\"为空数组。"
        )

        return "\n".join(parts)
