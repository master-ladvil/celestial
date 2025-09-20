import json
import asyncio
import os
from source.io.celestialVoice import CelestialVoice
from source.io.transcribe import CelestialEar
from source.tools.invocation.tools import get_current_time, open_application, search_internet
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from source.LlmConnectors.LlmConnectorMap import get_llm
from source.util.logger import logger
from source.core.agent.v2.agent import CelestialAgent

script_dir = os.path.dirname(__file__)
config_path = os.path.join(script_dir, "config/main/mainConfig.json")

def load_config_data():
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logger.critical(f"Error while getting config file: {e}")
        return None


async def process_and_speak(user_input,voice,agent):
    """Gets agent response and speak"""
    try:
        response  = await agent.get_response(user_input=user_input)
        await voice.speak(response)
    except asyncio.CancelledError:
        logger.info("Response task was cancelled successfully")
    except Exception as e:
        logger.error(f"Error During agent Response {e}")

@DeprecationWarning
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

async def main_interactive_loop(voice,ear,config_data):
    """
    Initializes the agent and runs the main interactive loop.
    """
    logger.info("Initializing agent for interactive session...")

    llm = get_llm(config_data["llmDetails"])
    tools=[get_current_time,open_application,search_internet]

    celestial_agent = CelestialAgent(llm=llm,tools=tools)
    await voice.speak("Celestial Activated... How can i Help?")

    speaking_task=None
    while True:
        user_input = await ear.listen()
        if user_input:
            if speaking_task and not speaking_task.done():
                logger.info("Interrupting previous Response.")
                speaking_task.cancel()
                await voice.stop()

            if any(word in user_input.lower() for word in ["terminate","exit","quit"]):
                await voice.speak("Quitting...")
                break

            speaking_task = asyncio.create_task(
                process_and_speak(user_input=user_input,voice=voice,agent=celestial_agent)
            )

async def main():
    config_data = load_config_data()
    if not config_data:
        logger.error("Problem loading in config data..")
        return

    ear = None
    try:
        ear_properties = config_data["transcribe_properties"]
        ear=CelestialEar(transcribe_properties=ear_properties)

        voice_properties = config_data["audioOutDetails"]
        voice = CelestialVoice(rate=voice_properties["rate"],driver_name=voice_properties["driver_name"])

        await main_interactive_loop(voice,ear,config_data)

    except KeyError as e:
        logger.error(f"Configuration error: Missing key {e}.")
    except KeyboardInterrupt:
        logger.info("\n Program interupted by user")
    finally:
        if ear:
            logger.info("Shutting down listening threads")
            ear.stop()


if __name__ == "__main__":
    # This allows the script to be run as the main interactive assistant
        asyncio.run(main())

