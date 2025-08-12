from langchain_community.chat_models import ChatOllama

from source.LlmConnectors.llmConnectorsInterface import LlmConnectorsInterface

class LocalLlmConnector(LlmConnectorsInterface):

    def __init__(self, llm_details):
        self.llm_details = llm_details

    def connect(self):
        llm = ChatOllama(model=self.llm_details["local_model_name"], temperature=self.llm_details["temperature"])
        llm.invoke("hello")
        return llm