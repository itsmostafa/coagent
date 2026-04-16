# Hivemind: advisor strategy LLM framework
from hivemind.config import load_config, merge_cli_overrides
from hivemind.executor import ExecutorLoop
from hivemind.schemas import ExecutorResult, HivemindConfig

__all__ = [
    "load_config",
    "merge_cli_overrides",
    "ExecutorLoop",
    "HivemindConfig",
    "ExecutorResult",
]


def run_task(task: str, config: HivemindConfig | None = None) -> ExecutorResult:
    """Convenience function to run a task with the given config."""
    from hivemind.advisor import Advisor
    from hivemind.log import NullTraceLogger
    from hivemind.models import ModelClient
    from hivemind.policy import DecisionPolicy
    from hivemind.tracking import CostTracker

    if config is None:
        config = load_config()

    executor_client = ModelClient(config.executor, search=config.search)
    advisor_client = ModelClient(config.advisor, search=config.search)
    advisor = Advisor(advisor_client)
    policy = DecisionPolicy(config.policy)
    tracker = CostTracker()
    trace_logger = NullTraceLogger()

    loop = ExecutorLoop(
        executor_client=executor_client,
        advisor=advisor,
        policy=policy,
        tracker=tracker,
        trace_logger=trace_logger,
        config=config,
    )
    return loop.run(task)
