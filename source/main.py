import json
import subprocess
import time

from celestial.source.io.celestialVoice import CelestialVoice
from celestial.source.io.transcribe import CelestialEar
from langchain_community.chat_models import ChatOllama
from celestial.source.tools.invocation.tools import get_current_time, open_application, search_internet
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

def checkOllama(config_data):
    llmDetails = config_data["llmDetails"]
    llm = ChatOllama(model=llmDetails["model"], temperature=llmDetails["temperature"])
    llm.invoke("hello")
    return llm

def load_config_data():
    try:
        with open("config/main/mainConfig.json",'r') as file:
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

    try:
        llm = checkOllama(config_data)
    except Exception as e:
        voice.speak("Error connection to Ollama. Please make sure ollama server is running and the model is pulled,.  do you want to try starting it?")
        ollamastart = ear.listen()
        if("yes" in ollamastart):
            try:
                voice.speak("trying to start Ollama...")
                subprocess.run("ollama serve")
                time.sleep(5)
                checkOllama(config_data)
            except Exception as e:
                voice.speak(f"Could not start ollama hope the model is not installed Exception : {e}")
                exit()
        else :
            print(f"Exception : {e}")
            exit()

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
