from source.LlmConnectors.local.celestialOllamaConnector import LocalLlmConnector
from source.LlmConnectors.online.celestialOpenAiConnector import CelestialOpenAiConnector


AVAILABLE_CONNECTORS = {
    "local_ollama": LocalLlmConnector,
    "online_openai": CelestialOpenAiConnector,
    # To add a new connector for Anthropic's Claude, you'd just add:
    # "online_claude": ClaudeLlmConnector,
}

def getConnectorClass(connectorName,llm_details):
    return AVAILABLE_CONNECTORS.get(connectorName, None)

def get_llm(llm_details):
    connector_name = llm_details.get("connector_name")
    if not connector_name:
        raise ValueError("Config error: 'llmConnectorType' not specified.")

    # Find the correct connector class in our map
    connector_class = AVAILABLE_CONNECTORS.get(connector_name)
    if not connector_class:
        raise ValueError(f"Unknown connector type: '{connector_name}'.")

    # 1. Create an INSTANCE of the connector class
    connector_instance = connector_class(llm_details)

    # 2. Call the connect() method on the INSTANCE
    return  connector_instance.connect()

