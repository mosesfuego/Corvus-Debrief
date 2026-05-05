"""Coordinates connectors, domain agents, and debrief-ready context."""

from agent_runtime.context import AgentContext
from agent_runtime.registry import AgentRegistry
from agent_runtime.result import sort_findings
from connectors.factory import get_connector


class DebriefOrchestrator:
    """Builds compact manufacturing context from enabled domain agents."""

    def __init__(self, config: dict, onboarding: dict):
        self.config = config
        self.onboarding = onboarding
        self.connector = get_connector(config, onboarding)
        self.registry = AgentRegistry(config, onboarding)

    def load_builds(self) -> list[dict]:
        return self.connector.fetch_builds()

    def build_context(self) -> dict:
        raw_builds = self.load_builds()
        context = AgentContext(
            raw_builds=raw_builds,
            builds=raw_builds,
            config=self.config,
            onboarding=self.onboarding,
            source_type=self.config.get("mes_type"),
        )

        domains = {}
        agent_results = {}
        all_findings = []
        evaluated_builds = raw_builds
        work_order_context = {}
        agents = self.registry.build()

        for agent in agents:
            result = agent.evaluate(context)
            domain = result["domain"]
            agent_results[domain] = result

            if domain == "work_order":
                evaluated_builds = result.get("builds", raw_builds)
                context.builds = evaluated_builds
                work_order_context = result
                domains[domain] = {
                    key: value for key, value in result.items()
                    if key != "builds"
                }
            else:
                domains[domain] = result

            all_findings.extend(result.get("findings", []))

        ranked_findings = sort_findings(all_findings)
        summary = work_order_context.get("summary", {})
        signals = work_order_context.get("signals", {})

        return {
            "builds": evaluated_builds,
            "summary": summary,
            "signals": signals,
            "domains": domains,
            "findings": ranked_findings,
            "agent_results": agent_results,
            "agent_order": [agent.name for agent in agents],
        }
