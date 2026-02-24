<<<<<<< HEAD
from abc import ABC, abstractmethod

class BaseMESConnector(ABC):

    @abstractmethod
    def fetch_latest_builds(self):
=======
"""Base MES connector abstract class."""
from abc import ABC, abstractmethod


class BaseMESConnector(ABC):
    """Abstract base class for MES connectors."""

    def __init__(self, config: dict):
        """Initialize connector with configuration."""
        self.config = config

    @abstractmethod
    def fetch_builds(self) -> list[dict]:
        """Fetch builds from MES system.

        Returns:
            List of dictionaries with keys: build_id, start_time, end_time
        """
>>>>>>> origin/agent-dev
        pass
