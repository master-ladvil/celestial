import speech_recognition as sr

class CelestialEar:

    def __init__(self,chunk_size, pause_threshold,timeout,phrase_time_limit):
        self.recognizer = sr.Recognizer()
        self.chunk_size = chunk_size
        self.pause_threshold = pause_threshold
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit

    def listen(self):
        with sr.Microphone(chunk_size=self.chunk_size) as source:
            print("listening....")
            self.recognizer.pause_threshold = self.pause_threshold
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                audio = self.recognizer.listen(source)
                print("recognising....")
                command = self.recognizer.recognize_google(audio,language='en-us')
                print(f"you said : {command}")
                return command
            except sr.WaitTimeoutError:
                # This error is less likely without a timeout, but good practice to keep.
                print("Listening timed out while waiting for phrase to start.")
                return None
            except Exception as e:
                print(f"Error listening or recognising {e}")
                return None