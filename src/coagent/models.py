import logging
import uuid
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
        session_id = str(uuid.uuid4())
        completion_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "metadata": {"litellm_session_id": session_id},
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
            # completion_cost can fail when the API returns a versioned model snapshot
            # (e.g. "gpt-5.4-mini-2026-03-05") not in litellm's cost map.
            # Fall back to computing cost from the configured model name, which
            # litellm.get_model_info() resolves correctly (handles "openai/" prefix).
            try:
                model_info = litellm.get_model_info(self.model)
                cost = prompt_tokens * (
                    model_info.get("input_cost_per_token") or 0.0
                ) + completion_tokens * (model_info.get("output_cost_per_token") or 0.0)
            except Exception:
                # Cost calculation not available for this model (e.g. local Ollama)
                pass

        return ModelResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            model=self.model,
        )
