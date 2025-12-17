import asyncio
import sys
from source.util.logger import logger

class CelestialConsole:
    """
        Text-based IO handler for the Celestial Agent.
        Implements the same interface as CelestialEar and CelestialVoice.
    """

    def __init__(self):
        pass

    async def listen(self):
        """
            Asynchronously gets user input from the console.
            Uses asyncio.to_thread to prevent blocking the event loop.
        """
        try:
            print("\n Type your message (or 'exit' to quit):  ")
            user_input = await asyncio.to_thread(input, "You : ")
            return user_input.strip()
        except Exception as e:
            logger.error(f"Console input error : {e}")
            return "exit"

    async def speak(self,text):
        print(f"\n Celestial : {text}\n")

    async def stop(self):
        pass

class CompositeVoice:
    """
        Multiplexes output to multiple voice/output handlers (e.g., TTS and Console).
    """
    def __init__(self,voices):
        self.voices = voices

    async def speak(self,text):
        """
            Broadcasts the text to all registered voice handlers concurrently.
        """
        await asyncio.gather(*(voice.speak(text) for voice in self.voices))

    async def stop(self):
        await asyncio.gather(*(voice.stop() for voice in self.voices))

