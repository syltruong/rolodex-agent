import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]

# "openai" or "local"
LLM_BACKEND: str = os.getenv("LLM_BACKEND", "openai")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

# MLX LM server (mlx_lm.server --model <path> --port 8080)
LOCAL_BASE_URL: str = os.getenv("LOCAL_BASE_URL", "http://localhost:8080/v1")
LOCAL_MODEL: str = os.getenv("LOCAL_MODEL", "local-model")
LOCAL_API_KEY: str = os.getenv("LOCAL_API_KEY", "not-needed")

def _load_system_prompt() -> str:
    if env_val := os.getenv("SYSTEM_PROMPT"):
        return env_val
    default_file = Path(__file__).parent / "system_prompt.md"
    if default_file.exists():
        return default_file.read_text(encoding="utf-8")
    return "You are a helpful personal assistant."

SYSTEM_PROMPT: str = _load_system_prompt()

# Absolute path to the root of your Obsidian vault
OBSIDIAN_VAULT_ROOT: str = os.getenv("OBSIDIAN_VAULT_ROOT", "")


def build_model() -> OpenAIChatCompletionsModel:
    """Return the active chat-completions model based on LLM_BACKEND."""
    if LLM_BACKEND == "local":
        client = AsyncOpenAI(base_url=LOCAL_BASE_URL, api_key=LOCAL_API_KEY)
        model_name = LOCAL_MODEL
    else:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        model_name = OPENAI_MODEL
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)
