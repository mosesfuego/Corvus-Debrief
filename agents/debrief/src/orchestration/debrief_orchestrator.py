"""Coordinates connectors, domain agents, and debrief-ready context."""

from connectors.factory import get_connector
from domain_agents.materials_lite_agent import MaterialsLiteAgent
from domain_agents.quality_lite_agent import QualityLiteAgent
from domain_agents.work_order_agent import WorkOrderAgent


class DebriefOrchestrator:
    """Builds compact manufacturing context from one or more domain agents."""

    def __init__(self, config: dict, onboarding: dict):
        self.config = config
        self.onboarding = onboarding
        self.connector = get_connector(config, onboarding)
        self.work_orders = WorkOrderAgent(config, onboarding)
        self.quality = QualityLiteAgent()
        self.materials = MaterialsLiteAgent()

    def load_builds(self) -> list[dict]:
        return self.connector.fetch_builds()

    def build_context(self) -> dict:
        raw_builds = self.load_builds()
        work_order_context = self.work_orders.evaluate(raw_builds)
        evaluated_builds = work_order_context["builds"]
        quality_context = self.quality.evaluate(evaluated_builds)
        materials_context = self.materials.evaluate(evaluated_builds)
        compact_work_order_context = {
            key: value for key, value in work_order_context.items()
            if key != "builds"
        }

        return {
            "builds": evaluated_builds,
            "summary": work_order_context["summary"],
            "signals": work_order_context["signals"],
            "domains": {
                "work_order": compact_work_order_context,
                "quality": quality_context,
                "materials": materials_context,
            },
            "findings": (
                work_order_context.get("findings", [])
                + quality_context.get("findings", [])
                + materials_context.get("findings", [])
            ),
        }
