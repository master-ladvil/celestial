import json

import asyncio
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

async def respond_and_speak(inp, current_voice, current_agent_executor):
    try:
        response = await current_agent_executor.ainvoke({"input" : inp})
        await current_voice.speak(response['output'])
    except asyncio.CancelledError:
        print("Response task was cancelled successfully. ")
    except Exception as e:
        print(f"Error during agent response : {e}")


async def main():
    config_data = load_config_data()
    if not config_data:
        print("Exitting : Could not load configuration properties")
        return

    # --- Initialise IO ---
    try:

        ear_properties = config_data["transcribeProperties"]
        ear = CelestialEar(ear_properties)

        voice_properties = config_data["audioOutDetails"]
        voice = CelestialVoice(voice_properties["rate"],voice_properties["driver_name"])

        llmDetails = config_data["llmDetails"]
    except KeyError as e:
        print(f"Configuration error keys missing: Missing key {e}")
        return

    # --- Agent Logic ---
    try:
        llm = get_llm(llmDetails)
    except Exception as e:
        print(f"Failed to initialise LLM : {e}")
        await voice.speak("I am having trouble loading and initializing the language model, please check the configuration and logs")
        return

    tools=[get_current_time,open_application,search_internet]

    # --- Load prompt from file ---
    prompt_file_path = os.path.join(script_dir, llmDetails["promptFileLocation"])
    try:
        with open(prompt_file_path,'r') as promptFile:
            prompt_template = promptFile.read()
    except Exception as e:
        print(f"Prompt file cannot be found at the location : {prompt_file_path}")
        await voice.speak("I am facing problem during prompt file loading please check if the path is correct in the logs.. quitting...")
        return

    prompt = PromptTemplate.from_template(prompt_template)

    # --- Creating agent ---
    agent = create_react_agent(llm,tools,prompt)
    agent_executor = AgentExecutor(agent=agent,tools=tools,verbose=True)

    await voice.speak("Celestial activated..., How can i help?")

    speaking_task = None


    # --- Main Async Loop ---
    while True:
        user_inptut = await ear.listen()
        if user_inptut:
            if speaking_task and not speaking_task.done():
                print("Interupting previous response.")
                speaking_task.cancel()
                await voice.stop()

            if any(word in user_inptut.lower() for word in ["terminate", "exit"]):
                await voice.speak("Quitting....")
                ear.stop()
                break

            speaking_task = asyncio.create_task(respond_and_speak(user_inptut,voice,agent_executor))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Program interupted by user.")