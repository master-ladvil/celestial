import multiprocessing

import pyttsx3


def speak_proccess_target(text,driver_name,rate):
    print(f"Celestial : {text}")
    try:
        engine = pyttsx3.init(driverName=driver_name)
        engine.setProperty('rate', rate)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"TTS Process Error: {e}")



class CelestialVoice:

    def __init__(self, rate,driver_name):
        self.rate = rate
        self.driver_name = driver_name


    def speak(self,text):
        process = multiprocessing.Process(target=speak_proccess_target,args=(text,self.driver_name,self.rate))
        process.start()
        process.join()
