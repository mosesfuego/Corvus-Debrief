"""Base protocol for Corvus manufacturing domain agents."""

from abc import ABC, abstractmethod

from agent_runtime.context import AgentContext


class DomainAgent(ABC):
    """Base class for specialized manufacturing agents."""

    name: str
    domain: str

    @abstractmethod
    def evaluate(self, context: AgentContext | list[dict]) -> dict:
        """Evaluate the available manufacturing context."""

