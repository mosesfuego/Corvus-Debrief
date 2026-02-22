from abc import ABC, abstractmethod

class BaseMESConnector(ABC):

    @abstractmethod
    def fetch_latest_builds(self):
        pass
