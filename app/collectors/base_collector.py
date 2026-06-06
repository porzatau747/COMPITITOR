from abc import ABC, abstractmethod
class BaseCollector(ABC):
    @abstractmethod
    def collect(self, db, hours: int = 24) -> list: ...
