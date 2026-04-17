# Hivemind

Hivemind implements the **advisor strategy** pattern: a cheap executor model handles tasks turn-by-turn, while a powerful advisor model is consulted only when the executor signals it needs help. The result is frontier-level performance at a fraction of the cost.

The typical setup pairs a local model as the executor with a state-of-the-art model (`claude-opus-4-6`, `gpt-5.4`) as the advisor. The advisor is called sparingly, not on every turn.

Reference: https://claude.com/blog/the-advisor-strategy

**Requires [uv](https://github.com/astral-sh/uv)** — install it with `curl -LsSf https://astral.sh/uv/install.sh | sh`.

## Quick Start

### Install

```bash
uv tool install git+https://github.com/itsmostafa/hivemind
```

This makes `hivemind` available as a command in your PATH. Requires [uv](https://docs.astral.sh/uv/).

To install from a local clone:

```bash
git clone https://github.com/itsmostafa/hivemind
uv tool install ./hivemind
```

### Run from CLI

```bash
# Create your user config (run once after install)
hivemind init
# Edit ~/.hivemind/config.yml to set your models and API keys

# One-shot task
hivemind run --executor ollama/llama3.2 --advisor openai/gpt-5.4 "Explain REST vs GraphQL tradeoffs"

# With an OpenAI-compatible endpoint (e.g. LM Studio)
hivemind run \
  --executor openai/local-model --executor-api-base http://localhost:1234/v1 \
  --advisor openai/gpt-5.4 \
  "Write a CSV parser in Python"

# With user config (auto-loaded from ~/.hivemind/config.yml)
hivemind run "Write a CSV parser in Python"

# Interactive chat REPL — conversation history is preserved across turns
hivemind chat
hivemind chat --executor ollama/llama3.2 --advisor openai/gpt-5.4

# View a trace
hivemind trace traces/run.jsonl
```

### Chat REPL

`hivemind chat` opens an interactive session. The executor+advisor pipeline runs on each message and conversation history carries over between turns so follow-up questions have full context.

```
hivemind chat  (q=quit, r=reset, h=help)
Executor Model: ollama/llama3.2  Advisor Model: openai/gpt-5.4  Web Search: Off
>> Explain the adapter pattern
...
>> Now show me an example in Go
...
>> r
[session reset]
>> 
```

| Command | Action |
|---------|--------|
| `q` / `quit` / `exit` | End the session and print cumulative usage |
| `r` / `reset` | Clear conversation history and start fresh |
| `h` / `help` | Show available commands |
| Ctrl-C / Ctrl-D | Exit immediately |

All CLI flags from `hivemind run` are available (`--executor`, `--advisor`, `--executor-api-base`, `--advisor-api-base`, `--trace`, `--search`) except `--force-consult`.

### Python API

```python
from hivemind import run_task, load_config
from hivemind.schemas import hivemindConfig, ModelConfig

config = hivemindConfig(
    executor=ModelConfig(model="ollama/llama3.2", api_base="http://localhost:11434"),
    advisor=ModelConfig(model="openai/gpt-5.4", api_key="..."),
)

result = run_task("Explain REST vs GraphQL tradeoffs", config=config)
print(result.final_answer)
print(result.usage_summary)
```

## Configuration

hivemind loads `~/.hivemind/config.yml` automatically — no flag required. Run `hivemind init` once to scaffold it from the default template, then edit it with your models and API keys.

The template (also available as `config.example.yaml` in the repo) looks like this:

```yaml
executor:
  model: "ollama/llama3.2"
  api_base: "http://localhost:11434"

advisor:
  model: "openai/gpt-5.4"
  api_key: "${OPENAI_API_KEY}"

policy:
  max_advisor_calls: 5
  failure_threshold: 2
  confidence_threshold: 0.4
  stagnation_turns: 4
  cooldown_turns: 2

max_turns: 20
logging:
  level: "INFO"
  trace_file: "traces/run.jsonl"

# Optional: Tavily web search tool (models decide when to use it)
search:
  enabled: true
  # api_key is optional — TavilyClient reads TAVILY_API_KEY from env automatically
```

## Architecture

```
User → CLI / Python API → ExecutorLoop
                              │
                    generate() via LiteLLM → Executor Model
                              │
                    DecisionPolicy.should_consult()
                              │
                    (if triggered) → Advisor Model
                              │
                    Parse AdvisorResponse (Pydantic)
                              │
                    Inject guidance → back to Executor
```

The executor is always in control. The advisor is a consulted resource — it never produces user-facing output.

## Advisor Triggers

The advisor is consulted when any of these fire:

| Trigger | Condition |
|---------|-----------|
| Explicit request | Executor outputs `[NEED_ADVICE]` |
| Consecutive failures | N turns with failure signals |
| Low confidence | Executor reports `[CONFIDENCE:0.3]` below threshold |
| Stagnation | Last N responses have high text overlap |

Gates prevent over-consulting: budget cap (`max_advisor_calls`) and cooldown (`cooldown_turns`).

## Supported Models

Any model supported by [LiteLLM](https://docs.litellm.ai/docs/providers):

- Local: `ollama/llama3`, `ollama/mistral`
- OpenAI: `openai/gpt-5.4`, `openai/gpt-5.4-mini`
- Anthropic: `anthropic/claude-sonnet-4-6`
- OpenAI-compatible: set `api_base` in config, or pass `--executor-api-base` / `--advisor-api-base` via CLI

## Web Search

Enable Tavily web search so models can look up current information at their own discretion:

```bash
# Via CLI flag
TAVILY_API_KEY=tvly-xxx hivemind run --search "What are the top AI papers this week?"

# Via config (search.enabled: true in ~/.hivemind/config.yml)
TAVILY_API_KEY=tvly-xxx hivemind run "What are the top AI papers this week?"
```

The model decides when to call the search tool (`tool_choice="auto"`). It is never forced. Get a free API key at [tavily.com](https://tavily.com).

## Development

```bash
uv sync
uv run pytest tests/ -v
uv run ruff check src/ tests/
```

## Limitations (MVP)

- Synchronous only (no streaming or async)
- Single advisor model
