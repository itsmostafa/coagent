import pytest


@pytest.fixture
def sample_task():
    return "Explain the tradeoffs between REST and GraphQL"


@pytest.fixture
def minimal_config():
    return {}


@pytest.fixture
def policy_config():
    from coagent.schemas import PolicyConfig
    return PolicyConfig(max_advisor_calls=3, failure_threshold=2, stagnation_turns=3, cooldown_turns=1)
