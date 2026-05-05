"""Registry for enabled manufacturing domain agents."""

from collections.abc import Callable

from domain_agents.labor.agent import LaborAgent
from domain_agents.materials.agent import MaterialsAgent
from domain_agents.quality.agent import QualityAgent
from domain_agents.schedule.agent import ScheduleAgent
from domain_agents.work_order.agent import WorkOrderAgent

DEFAULT_AGENT_ORDER = [
    "work_order",
    "materials",
    "quality",
    "schedule",
    "labor",
]


def _work_order_factory(config: dict, onboarding: dict):
    return WorkOrderAgent(config, onboarding)


AGENT_FACTORIES: dict[str, Callable[[dict, dict], object]] = {
    "work_order": _work_order_factory,
    "materials": lambda _config, _onboarding: MaterialsAgent(),
    "quality": lambda _config, _onboarding: QualityAgent(),
    "schedule": lambda _config, _onboarding: ScheduleAgent(),
    "labor": lambda _config, _onboarding: LaborAgent(),
}


class AgentRegistry:
    """Builds enabled domain-agent instances for a customer run."""

    def __init__(self, config: dict | None = None, onboarding: dict | None = None):
        self.config = config or {}
        self.onboarding = onboarding or {}

    def enabled_names(self) -> list[str]:
        configured = (
            self.config.get("domain_agents", {}).get("enabled")
            or self.config.get("agents", {}).get("enabled_domain_agents")
            or DEFAULT_AGENT_ORDER
        )
        names = [name for name in configured if name in AGENT_FACTORIES]
        if "work_order" not in names:
            names.insert(0, "work_order")
        return names

    def build(self) -> list[object]:
        """Instantiate enabled agents in deterministic execution order."""
        ordered = []
        enabled = set(self.enabled_names())
        for name in DEFAULT_AGENT_ORDER:
            if name in enabled:
                ordered.append(AGENT_FACTORIES[name](self.config, self.onboarding))
        return ordered

