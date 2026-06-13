import logging
from agents import Agent, Runner
from agents.lifecycle import RunHooksBase
from agents.run_context import RunContextWrapper
from agents.tool import Tool
import config
from tools import ALL_TOOLS

logger = logging.getLogger("rolodex.tools")


class _LoggingHooks(RunHooksBase):
    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        args = getattr(context, "tool_arguments", None)
        if args:
            logger.info("[tool] → %s  args=%s", tool.name, args)
        else:
            logger.info("[tool] → %s", tool.name)

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: object) -> None:
        preview = str(result)
        if len(preview) > 120:
            preview = preview[:120] + "…"
        logger.info("[tool] ← %s  result=%s", tool.name, preview)


_HOOKS = _LoggingHooks()


def build_agent() -> Agent:
    return Agent(
        name="rolodex",
        model=config.build_model(),
        instructions=config.SYSTEM_PROMPT,
        tools=ALL_TOOLS,
    )


class ConversationManager:
    """Maintains per-chat history across Telegram turns using the Agents SDK."""

    def __init__(self, agent: Agent) -> None:
        self._agent = agent
        self._histories: dict[int, list] = {}

    async def respond(self, chat_id: int, user_text: str) -> str:
        history = self._histories.get(chat_id, [])
        result = await Runner.run(
            self._agent,
            input=history + [{"role": "user", "content": user_text}],
            hooks=_HOOKS,
        )
        self._histories[chat_id] = result.to_input_list()
        return result.final_output or "(empty response)"

    def clear(self, chat_id: int) -> None:
        self._histories.pop(chat_id, None)
