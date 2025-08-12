from abc import ABC, abstractmethod
class LlmConnectorsInterface(ABC):

    @abstractmethod
    def connect(self):
        """Implement the connector logic to the needed models"""
        pass