import json
import asyncio
import os
from source.io.celestialVoice import CelestialVoice
from source.io.transcribe import CelestialEar
from source.io.console import CelestialConsole, CompositeVoice
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


def get_io_components(config_data):
    """
    Factory function to initialize the correct IO components based on configuration.
    """
    io_config = config_data.get("io", {"input_mode": "voice", "output_mode": ["voice"]})

    # --- Setup Input (Ear) ---
    input_mode = io_config.get("input_mode", "voice")
    if input_mode == "text":
        logger.info("Input mode: Text (Console)")
        ear = CelestialConsole()
    else:
        logger.info("Input mode: Voice (Whisper)")
        ear_properties = config_data["transcribe_properties"]
        ear = CelestialEar(transcribe_properties=ear_properties)

    # --- Setup Output (Voice) ---
    output_modes = io_config.get("output_mode", ["voice"])
    voices = []

    if "text" in output_modes:
        logger.info("Output mode added: Text (Console)")
        voices.append(CelestialConsole())

    if "voice" in output_modes:
        logger.info("Output mode added: Voice (TTS)")
        voice_properties = config_data["audioOutDetails"]
        voices.append(CelestialVoice(rate=voice_properties["rate"], driver_name=voice_properties["driver_name"]))

    # If multiple outputs are selected, use CompositeVoice to handle them together
    if len(voices) > 1:
        voice = CompositeVoice(voices)
    elif len(voices) == 1:
        voice = voices[0]
    else:
        # Fallback default
        logger.warning("No output mode specified, defaulting to Console.")
        voice = CelestialConsole()

    return ear, voice


async def process_and_speak(user_input, voice, agent):
    """Gets agent response and speak"""
    try:
        response = await agent.get_response(user_input=user_input)
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


async def main_interactive_loop(voice, ear, config_data):
    """
    Initializes the agent and runs the main interactive loop.
    """
    logger.info("Initializing agent for interactive session...")

    llm = get_llm(config_data["llmDetails"])
    tools = [get_current_time, open_application, search_internet]

    celestial_agent = CelestialAgent(llm=llm, tools=tools)
    await voice.speak("Celestial Activated... How can i Help?")

    # Determine the input mode from config
    input_mode = config_data.get("io", {}).get("input_mode", "voice")

    speaking_task = None
    while True:
        # ear.listen() is polymorphic! It handles both text and voice.
        user_input = await ear.listen()

        if user_input:
            if speaking_task and not speaking_task.done():
                logger.info("Interrupting previous Response.")
                speaking_task.cancel()
                await voice.stop()

            if any(word in user_input.lower() for word in ["terminate", "exit", "quit"]):
                await voice.speak("Quitting...")
                break

            # If in text mode, we wait for the agent to finish before asking again (Cleaner UI)
            if input_mode == "text":
                await process_and_speak(user_input=user_input, voice=voice, agent=celestial_agent)
            else:
                # In voice mode, we run in background to allow interruptions
                speaking_task = asyncio.create_task(
                    process_and_speak(user_input=user_input, voice=voice, agent=celestial_agent)
                )


async def main():
    config_data = load_config_data()
    if not config_data:
        logger.error("Problem loading in config data..")
        return

    ear = None
    voice = None
    try:
        # Use the factory function to get the correct components
        ear, voice = get_io_components(config_data)

        await main_interactive_loop(voice, ear, config_data)

    except KeyError as e:
        logger.error(f"Configuration error: Missing key {e}.")
    except KeyboardInterrupt:
        logger.info("\n Program interupted by user")
    finally:
        if ear:
            logger.info("Shutting down listening threads")
            ear.stop()
        # Ensure we stop the voice processing as well if needed
        if voice:
            await voice.stop()


if __name__ == "__main__":
    # This allows the script to be run as the main interactive assistant
    asyncio.run(main())