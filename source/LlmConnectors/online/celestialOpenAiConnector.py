from langchain_openai import ChatOpenAI

from source.LlmConnectors.llmConnectorsInterface import LlmConnectorsInterface
from dotenv import load_dotenv

class CelestialOpenAiConnector(LlmConnectorsInterface):

    def __init__(self, config):
        self.config = config

    def connect(self):
        load_dotenv()
        llm = ChatOpenAI(model=self.config["online_model_name"],temperature=self.config["temperature"])
        llm.invoke("hello")
        return llm