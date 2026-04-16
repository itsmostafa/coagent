import os
import re
from pathlib import Path
from typing import Any

import yaml

from hivemind.schemas import HivemindConfig, ModelConfig

USER_CONFIG_PATH = Path.home() / ".hivemind" / "config.yml"


def _expand_env_vars(value: str) -> str:
    """Expand ${ENV_VAR} references in a string value."""

    def replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return re.sub(r"\$\{([^}]+)\}", replace, value)


def _expand_env_vars_in_dict(data: Any) -> Any:
    """Recursively expand ${ENV_VAR} references in all string values of a dict."""
    if isinstance(data, dict):
        return {k: _expand_env_vars_in_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_expand_env_vars_in_dict(item) for item in data]
    elif isinstance(data, str):
        return _expand_env_vars(data)
    else:
        return data


def load_config(path: str | None = None) -> HivemindConfig:
    """Load HivemindConfig from a YAML file.

    If path is None, looks for ~/.hivemind/config.yml. If it does not exist,
    returns a default config.
    Expands ${ENV_VAR} references in string values.
    Validates with Pydantic.
    """
    if path is None:
        if USER_CONFIG_PATH.exists():
            path = str(USER_CONFIG_PATH)

    if path is None:
        return HivemindConfig(
            executor=ModelConfig(model="ollama/llama3"),
            advisor=ModelConfig(model="ollama/llama3"),
        )

    with open(path) as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raw = {}

    raw = _expand_env_vars_in_dict(raw)
    return HivemindConfig.model_validate(raw)


def merge_cli_overrides(
    config: HivemindConfig,
    executor: str | None = None,
    advisor: str | None = None,
    executor_api_base: str | None = None,
    advisor_api_base: str | None = None,
    force_consult: bool = False,
    search_enabled: bool | None = None,
) -> HivemindConfig:
    """Return a new HivemindConfig with CLI overrides applied.

    executor and advisor are model strings (e.g. "ollama/llama3").
    executor_api_base and advisor_api_base set the API endpoint for each model.
    force_consult forces advisor consultation on the first policy check.
    search_enabled enables Tavily web search tool when True.
    None means "no override, keep config value".
    """
    data = config.model_dump()
    if executor is not None:
        data["executor"]["model"] = executor
    if advisor is not None:
        data["advisor"]["model"] = advisor
    if executor_api_base is not None:
        data["executor"]["api_base"] = executor_api_base
    if advisor_api_base is not None:
        data["advisor"]["api_base"] = advisor_api_base
    if force_consult:
        data["policy"]["force_consult"] = True
    if search_enabled is not None:
        data["search"]["enabled"] = search_enabled
    return HivemindConfig.model_validate(data)
