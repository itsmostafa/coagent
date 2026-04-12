"""Tests for Pydantic model validation in coagent.schemas."""
import pytest
from pydantic import ValidationError

from coagent.schemas import (
    AdvisorResponse,
    CoagentConfig,
    ExecutorResult,
    ExecutorState,
    ModelConfig,
    ModelResponse,
    PolicyConfig,
)


def test_model_response_valid():
    resp = ModelResponse(
        content="hello world",
        prompt_tokens=10,
        completion_tokens=5,
        cost=0.001,
        model="test/model",
    )
    assert resp.content == "hello world"
    assert resp.prompt_tokens == 10
    assert resp.completion_tokens == 5
    assert resp.cost == 0.001
    assert resp.model == "test/model"


def test_advisor_response_status_validation():
    with pytest.raises(ValidationError):
        AdvisorResponse(
            status="invalid_status",
            diagnosis="something went wrong",
            confidence=0.8,
        )


def test_policy_config_defaults():
    config = PolicyConfig()
    assert config.max_advisor_calls == 5
    assert config.failure_threshold == 2
    assert config.confidence_threshold == 0.4
    assert config.stagnation_turns == 4
    assert config.cooldown_turns == 2


def test_coagent_config_defaults():
    config = CoagentConfig(
        executor=ModelConfig(model="ollama/llama3"),
        advisor=ModelConfig(model="ollama/llama3"),
    )
    assert config.max_turns == 20
    assert isinstance(config.policy, PolicyConfig)
    assert config.policy.max_advisor_calls == 5
    assert config.logging.level == "INFO"
    assert config.logging.trace_file is None


def test_executor_state_defaults():
    state = ExecutorState(task="do something")
    assert state.turn_number == 0
    assert state.status == "running"
    assert state.advisor_calls == 0
    assert state.messages == []
    assert state.advisor_history == []


def test_executor_result_roundtrip():
    state = ExecutorState(task="compute 2+2", status="completed")
    result = ExecutorResult(
        final_answer="4",
        state=state,
        usage_summary={"executor": {}, "advisor": {}, "total": {}},
        advisor_history=[],
    )
    assert result.final_answer == "4"
    assert result.state.task == "compute 2+2"
    assert result.state.status == "completed"
    assert result.usage_summary["total"] == {}
    assert result.advisor_history == []
