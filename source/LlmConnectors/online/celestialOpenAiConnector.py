from langchain_community.chat_models import ChatOpenAI

from source.LlmConnectors.llmConnectorsInterface import LlmConnectorsInterface

class CelestialOpenAiConnector(LlmConnectorsInterface):

    def __init__(self, config):
        self.config = config

    def connect(self):
        llm = ChatOpenAI(model=self.config["online_model_name"],temperature=self.config["temperature"],api_key=self.config["api_key"])
        llm.invoke("hello")
        return llm