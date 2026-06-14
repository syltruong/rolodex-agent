# rolodex-agent

A personal Telegram bot backed by the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python). It can route requests to OpenAI's API **or** a locally-served model via [mlx-lm](https://github.com/ml-explore/mlx-lm) or [Ollama](https://ollama.com), making it fully offline-capable on Apple Silicon.

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- For local inference: [mlx-lm](https://github.com/ml-explore/mlx-lm) (Apple Silicon) or [Ollama](https://ollama.com) (any platform)

---

## Installation

```bash
git clone <repo-url>
cd rolodex-agent
uv sync
```

---

## Configuration

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | *(required)* | Token from @BotFather |
| `LLM_BACKEND` | `openai` | `openai` or `local` |
| `OPENAI_API_KEY` | | Required when `LLM_BACKEND=openai` |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model name |
| `LOCAL_BASE_URL` | `http://localhost:8080/v1` | MLX LM server URL |
| `LOCAL_MODEL` | `local-model` | Model name sent in requests |
| `LOCAL_API_KEY` | `not-needed` | Placeholder (mlx-lm ignores it) |
| `OBSIDIAN_VAULT_ROOT` | | Absolute path to your Obsidian vault |
| `SYSTEM_PROMPT` | | Override default system prompt inline |

---

## Serving a model locally with MLX

### 1. Install mlx-lm

```bash
uv add mlx-lm
```

Or, to keep it isolated:

```bash
uv tool install mlx-lm
```

### 2. Choose a model

Models must be in MLX format. The easiest source is the [mlx-community](https://huggingface.co/mlx-community) org on Hugging Face — models are downloaded automatically on first run.

Recommended starting points:

| Model | HF repo | VRAM (approx.) |
|---|---|---|
| Qwen2.5 7B (4-bit) | `mlx-community/Qwen2.5-7B-Instruct-4bit` | ~4.3 GB |
| Mistral 7B (4-bit) | `mlx-community/Mistral-7B-Instruct-v0.3-4bit` | ~4.1 GB |
| Llama 3.2 3B (4-bit) | `mlx-community/Llama-3.2-3B-Instruct-4bit` | ~1.8 GB |
| Gemma 4 12B (4-bit) | `mlx-community/gemma-4-12B-it-OptiQ-4bit` | ~10 GB |

### 3. Start the server

```bash
mlx_lm.server --model mlx-community/gemma-4-12B-it-OptiQ-4bit --port 8080
```

The server exposes an OpenAI-compatible `/v1/chat/completions` endpoint at `http://localhost:8080/v1`.


### 4. Point the bot at it

In your `.env`:

```dotenv
LLM_BACKEND=local
LOCAL_BASE_URL=http://localhost:8080/v1
LOCAL_MODEL=mlx-community/gemma-4-12B-it-OptiQ-4bit   # must match --model above
LOCAL_API_KEY=not-needed
```

`LOCAL_MODEL` is passed through in the request body; mlx-lm ignores it but it can be useful for logging.

---

## Serving a model locally with Ollama

[Ollama](https://ollama.com) works on macOS, Linux, and Windows and exposes the same OpenAI-compatible endpoint, so no code changes are needed.

### 1. Install Ollama

Download and install from [ollama.com](https://ollama.com)


### 2. Pull a model

For example, for Apple Silicon support (MLX)
```bash
ollama pull gemma4:e4b-mlx
```

Browse available models at [ollama.com/library](https://ollama.com/library).

### 3. Start the server

Ollama starts automatically on macOS after install. To start it manually:

```bash
ollama serve
```

The OpenAI-compatible endpoint is available at `http://localhost:11434/v1`.

### 4. Point the bot at it

In your `.env`:

```dotenv
LLM_BACKEND=local
LOCAL_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL=gemma4:e4b-mlx   # must match the name used in `ollama pull`
LOCAL_API_KEY=not-needed
```

---

## Running the bot

```bash
uv run python main.py
```

Then talk to the agent via Telegram, and watch your Obsidian vault get updated

---

## Project structure

```
rolodex-agent/
├── main.py            # entry point
├── agent.py           # Agent + ConversationManager
├── config.py          # env loading + model factory
├── bot/
│   ├── handler.py     # Telegram update handlers
│   └── formatting.py  # Markdown helpers
└── tools/
    ├── obsidian_tools.py
    ├── datetime_tools.py
    └── skill_tool.py
```
