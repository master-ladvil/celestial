import json
import asyncio
import os
from source.io.celestialVoice import CelestialVoice
from source.io.transcribe import CelestialEar
from source.tools.invocation.tools import get_current_time, open_application, search_internet
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from source.LlmConnectors.LlmConnectorMap import get_llm

script_dir = os.path.dirname(__file__)
config_path = os.path.join(script_dir, "config/main/mainConfig.json")

def load_config_data():
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error while getting config file: {e}")
        return None

async def initialize_agent():
    """
    Initializes and returns the agent_executor.
    This function is now the single source of truth for creating an agent.
    """
    config_data = load_config_data()
    if not config_data:
        raise ValueError("Could not load configuration for agent initialization.")

    llmDetails = config_data["llmDetails"]
    llm = get_llm(llmDetails)
    tools = [get_current_time, open_application, search_internet]

    prompt_file_path = os.path.join(script_dir, llmDetails["promptFileLocation"])
    with open(prompt_file_path, 'r') as promptFile:
        prompt_template = promptFile.read()

    prompt = PromptTemplate.from_template(prompt_template)
    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


async def respond_and_speak(inp, current_voice, current_agent_executor):
    """Core logic for responding to a single input."""
    try:
        response = await current_agent_executor.ainvoke({"input": inp})
        await current_voice.speak(response['output'])
    except asyncio.CancelledError:
        print("Response task was cancelled successfully.")
    except Exception as e:
        print(f"Error during agent response: {e}")


async def main_interactive_loop():
    """The main interactive loop for the user."""
    print("Initializing agent for interactive session...")
    agent_executor = await initialize_agent()
    config_data = load_config_data()

    print("Initializing I/O...")
    ear_properties = config_data["transcribeProperties"]
    ear = CelestialEar(ear_properties)

    voice_properties = config_data["audioOutDetails"]
    voice = CelestialVoice(voice_properties["rate"], voice_properties["driver_name"])

    await voice.speak("Celestial activated..., How can I help?")
    speaking_task = None

    try:
        while True:
            user_input = await ear.listen()
            if user_input:
                if speaking_task and not speaking_task.done():
                    print("Interrupting previous response.")
                    speaking_task.cancel()
                    await voice.stop()

                if any(word in user_input.lower() for word in ["terminate", "exit"]):
                    await voice.speak("Quitting....")
                    break

                speaking_task = asyncio.create_task(respond_and_speak(user_input, voice, agent_executor))
    finally:
        print("Shutting down listening threads...")
        ear.stop()


if __name__ == "__main__":
    # This allows the script to be run as the main interactive assistant
    try:
        asyncio.run(main_interactive_loop())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
