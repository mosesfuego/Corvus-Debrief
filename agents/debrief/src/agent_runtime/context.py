"""Runtime context passed to domain agents."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    """Shared manufacturing context available to every domain agent."""

    raw_builds: list[dict[str, Any]] = field(default_factory=list)
    builds: list[dict[str, Any]] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    onboarding: dict[str, Any] = field(default_factory=dict)
    source_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_builds(
        cls,
        builds: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
        onboarding: dict[str, Any] | None = None,
    ) -> "AgentContext":
        """Create context for callers that still pass raw build lists."""
        return cls(
            raw_builds=builds,
            builds=builds,
            config=config or {},
            onboarding=onboarding or {},
        )


def ensure_agent_context(
    context_or_builds: AgentContext | list[dict[str, Any]],
    config: dict[str, Any] | None = None,
    onboarding: dict[str, Any] | None = None,
) -> AgentContext:
    """Accept either the new context object or the legacy list input."""
    if isinstance(context_or_builds, AgentContext):
        return context_or_builds
    return AgentContext.from_builds(context_or_builds, config, onboarding)

