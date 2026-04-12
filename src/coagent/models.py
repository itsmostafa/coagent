import logging
from typing import Any
import litellm
from coagent.schemas import ModelConfig, ModelResponse

logger = logging.getLogger(__name__)

# Suppress litellm's verbose logging by default
litellm.suppress_debug_info = True


class ModelClient:
    """Thin wrapper around LiteLLM completion() that normalizes responses."""

    def __init__(self, config: ModelConfig) -> None:
        self.model = config.model
        self.api_base = config.api_base
        self.api_key = config.api_key

    def generate(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Send messages to the model and return a normalized response.

        If system is provided, prepend it as a {"role": "system", "content": system}
        message at the start of the messages list.
        """
        if system is not None:
            messages = [{"role": "system", "content": system}] + messages

        # Build litellm kwargs
        completion_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if self.api_base is not None:
            completion_kwargs["api_base"] = self.api_base
        if self.api_key is not None:
            completion_kwargs["api_key"] = self.api_key
        completion_kwargs.update(kwargs)

        response = litellm.completion(**completion_kwargs)

        # Extract content
        content = response.choices[0].message.content or ""

        # Extract token usage
        usage = response.usage
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0

        # Extract cost — litellm stores it in _hidden_params or response_cost
        cost = 0.0
        try:
            cost = litellm.completion_cost(completion_response=response) or 0.0
        except Exception:
            # Cost calculation not available for all models (e.g. local Ollama)
            pass

        return ModelResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            model=self.model,
        )
