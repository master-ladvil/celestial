import json

from source.io.celestialVoice import CelestialVoice
from source.io.transcribe import CelestialEar
from source.tools.invocation.tools import get_current_time, open_application, search_internet
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

import os

from source.LlmConnectors.LlmConnectorMap import get_llm

script_dir = os.path.dirname(__file__)
# Join that directory with the relative path to your config file
config_path = os.path.join(script_dir, "config/main/mainConfig.json")

def load_config_data():
    try:
        with open(config_path,'r') as file:
            config_data = json.load(file)
            return config_data
    except Exception as e:
        print(f"Error while getting config file : {e}")

if __name__ == "__main__":

    config_data = load_config_data()

    #     initialise IO
    ear_properties = config_data["transcribeProperties"]
    ear = CelestialEar(ear_properties["chunk_size"],ear_properties["pause_threshold"],ear_properties["timeout"],ear_properties["phrase_time_limit"])

    voice_properties = config_data["audioOutDetails"]
    voice = CelestialVoice(voice_properties["rate"],voice_properties["driver_name"])

    llmDetails = config_data["llmDetails"]

#     Agent Logic

    llm = get_llm(llmDetails)

    tools=[get_current_time,open_application,search_internet]

#     load prompt from file
    try:
        with open(llmDetails["promptFileLocation"],'r') as promptFile:
            prompt_template = promptFile.read()
    except Exception as e:
        print(f"Prompt file cannot be found at the location : {llmDetails["promptFileLocation"]}")
        exit()

    prompt = PromptTemplate.from_template(prompt_template)

#     creating agent
    agent = create_react_agent(llm,tools,prompt)
    agent_executor = AgentExecutor(agent=agent,tools=tools,verbose=True)

    voice.speak("Celestial activated..., How can i help?")

    while True:
        user_inptut = ear.listen()
        if user_inptut:
            if "terminate" in user_inptut or "exit" in user_inptut:
                voice.speak("Quitting....")
                break

            response = agent_executor.invoke({"input" : user_inptut})
            voice.speak(response['output'])
