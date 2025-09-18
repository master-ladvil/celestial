import asyncio
import torch
import whisper
import numpy as np
from queue import Queue
from threading import Thread, Event
import speech_recognition as sr
from source.util.logger import logger

class CelestialEar:

    def __init__(self,transcribe_properties):
        """
        Initializes the CelestialEar transcriber.

        Args:e
            model_name (str): The name of the Whisper model to use (e.g., "tiny.en", "base.en").
            energy_threshold (int): The energy level for considering audio as speech.
            pause_threshold (float): Seconds of non-speaking audio before a phrase is considered complete.
            phrase_time_limit (int): The maximum number of seconds to record a single phrase.
        """
        self.model_name = transcribe_properties["model_name"]
        self.energy_threshold = transcribe_properties["energy_threshold"]
        self.pause_threshold = transcribe_properties["pause_threshold"]
        self.phrase_time_limit = transcribe_properties["phrase_time_limit"]
        self.sample_rate = transcribe_properties["sample_rate"]
        self.timeout = transcribe_properties["timeout"]

        # Determine the device for Torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Whisper will run on {self.device}")

        #Load the whisper model
        logger.info(f"Loading Whisper model: {self.model_name}...")
        self.model = whisper.load_model(self.model_name, device=self.device)
        logger.info("Whisper loaded successfully...")

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = transcribe_properties["energy_threshold"]
        self.recognizer.pause_threshold = transcribe_properties["pause_threshold"]
        self.recognizer.dynamic_energy_threshold = False

        self.audio_queue = Queue()
        self.result_queue = Queue()
        self.stop_event = Event()

        self.processing_thread = Thread(target=self._process_audio)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def _listen_in_background(self):
        """
        Listens for audio in a background thread and puts the data into a queue.
        This is the target for the background listening thread.
        """
        with sr.Microphone(sample_rate=self.sample_rate) as source:
            logger.info("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source)
            logger.info("Listening...")

            while not self.stop_event.is_set():
                try:
                    audio_data = self.recognizer.listen(source,timeout=self.timeout,phrase_time_limit=self.phrase_time_limit)
                    self.audio_queue.put(audio_data)
                except sr.WaitTimeoutError:
                    continue #No speach detected
                except Exception as e:
                    logger.critical(f"Error in listening thread : {e}")

    def _process_audio(self):
        """
        This function runs in a dedicated thread, pulling audio data from one
        queue, transcribing it, and putting the result text into another queue.
        """
        while not self.stop_event.is_set():
            try:
                audio_data = self.audio_queue.get(timeout=1.0)
                logger.info("audio data received preparing for transcription...")

                raw_data = audio_data.get_raw_data()
                audio_np = np.frombuffer(raw_data,dtype=np.int16)

                #normalise the audio data to be between -1.0 and 1.0
                audio_fp32 = audio_np.astype(np.float32) / 32768.0

                result = self.model.transcribe(audio_fp32,fp16=torch.cuda.is_available())
                text = result['text'].strip()
                if text:
                    logger.info(f"You said: {text}")
                    self.result_queue.put(text)

                self.audio_queue.task_done()
            except Exception as e:
                continue

    async def listen(self):
        """
        The main async method to be called from the event loop.
        It starts the listening process and waits for a result.
        """
        if not hasattr(self,'listening_thread') or not self.listening_thread.is_alive():
            self.listening_thread = Thread(target=self._listen_in_background)
            self.listening_thread.daemon = True
            self.listening_thread.start()

        # Wait for result from processing thread
        loop = asyncio.get_running_loop()
        try:
            # Use run_in_executor to wait for the blocking get() because it waits for 1 sec if nothing in queue call without freezing the event loop
            command = await loop.run_in_executor(None, self.result_queue.get)
            return command
        except asyncio.CancelledError:
            logger.info("Listening task cancelled....")
            return None

    def stop(self):
        """ stop listening and processing threads"""
        self.stop_event.set()
        if hasattr(self,'listening_thread') and self.listening_thread.is_alive():
            self.listening_thread.join()
        if self.processing_thread.is_alive():
            self.processing_thread.join()
