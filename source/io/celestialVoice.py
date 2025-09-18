import multiprocessing
import pyttsx3
import asyncio
from source.util.logger import logger

def speak_proccess_target(text,driver_name,rate):
    logger.info(f"Celestial : {text}")
    try:
        engine = pyttsx3.init(driverName=driver_name)
        engine.setProperty('rate', rate)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        logger.error(f"TTS Process Error: {e}")



class CelestialVoice:

    def __init__(self, rate,driver_name):
        self.rate = rate
        self.driver_name = driver_name
        self.current_process = None


    async def speak(self,text):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None,self.core_speech,text)


    # --- Run the below code in separate thread as it will block the execution ---
    def core_speech(self,text):
        # If there's somehow a process still lingering, terminate it.
        if self.current_process and self.current_process.is_alive():
            logger.info("Terminating speech process")
            self.current_process.terminate()

        # create and store new process
        self.current_process = multiprocessing.Process(target=speak_proccess_target, args=(text, self.driver_name, self.rate))
        self.current_process.start()
        self.current_process.join()
        self.current_process = None

    async def stop(self):
        if self.current_process and self.current_process.is_alive():
            logger.info("Terminating speech process")
            self.current_process.terminate()
            await asyncio.sleep(0.1)
            self.current_process = None

