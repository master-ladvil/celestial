import subprocess
import os
from datetime import datetime

import pyttsx3
import speech_recognition as sr
from duckduckgo_search import DDGS as dgs

#lang chain imports
# TODO : study all possible agents from llangchain
from langchain_community.chat_models import ChatOllama
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

# CONFIGURATION
OLLAMA_MODEL = "llama3:8b"
PROMPT_FILE=""

# Initialising TTs and Recogniser
try :
    engine = pyttsx3.init()
    engine.setProperty('rate',180) # TODO : understand what it does
except Exception as e:
    print(f"Error initialising TTS: {e}")
    engine = None

recognizer = sr.Recognizer()

# core speech function
def speak(text):
    # converts text to speech
    print(f"Celestial : {text}")
    if engine:
        engine.say(text)
        engine.runAndWait()

def listen():
    """Listens to command"""
    with sr.Microphone(chunk_size=2048) as source:
        print("Listening...")
        recognizer.pause_threshold = 2
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source,timeout=5, phrase_time_limit=10)
            print("Recognising...")
            command = recognizer.recognize_google(audio,language='en-us')
            print(f"You said: {command} \n ")
            return command
        except Exception as e:
            print(f"Error listening or recognising {e}")
            return None

# --- AGENT TOOLS (No changes here) ---

@tool
def get_current_time() -> str:
    """Retruns the current time in  a human-readable format."""
    return datetime.now().strftime("%I:%M %p")

@tool
def open_application(app_name: str) -> str:
    """
    Opens an application on the user's computer.
    'app_name' should be the name of the application, e.g., 'Google Chrome', 'Notepad', 'Terminal'.
    """

    # This removes leading/trailing whitespace and any surrounding quotes
    clean_app_name = app_name.strip().strip("'\"")
    print(f"Attempting to open {clean_app_name}")
    try:
        if 'darwin' in os.sys.platform:
            subprocess.run(["open", "-a", clean_app_name],check=True)
        elif 'win32' in os.sys.platform:
            os.startfile(clean_app_name)
        else:
            subprocess.run(["xdg-open", app_name], check=True)
        return f"The application {clean_app_name} has been successfully opened."
    except Exception as e:
        return f"Error opening {clean_app_name}: {e}. The app might not be installed or the name is incorrect."

    # MAIN AGENT LOGIC
if __name__ == "__main__":
    try :
        llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.3) #lower temperature more classical higher temperature
        #ping the model to see if the connection is working
        llm.invoke("Hello")
    except Exception as e:
        speak("Error connection to Ollama. please make sure the Ollama application is running and the model is pulled")
        print(f"Connection error : {e}")
        exit()

        # define tools
    tools = [get_current_time,open_application]

    #load prompt from text file
    try:
        with open(PROMPT_FILE,'r') as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"Prompt file cannot be found at the location : {PROMPT_FILE}")
        exit()

    prompt = PromptTemplate.from_template(prompt_template)

    # create agent
    agent = create_react_agent(llm,tools,prompt)
    agent_executor = AgentExecutor(agent=agent,tools=tools, verbose=True) #shows the reasoning steps

    speak("Ollama assistant activated, How can i help you?")

    while True:
        user_input = listen()
        if user_input:
            if "terminate" in user_input.lower() or "exit" in user_input.lower():
                speak("Quitting")
                break

            #send the input to the agent and get the response
            response = agent_executor.invoke({"input": user_input})

            speak(response['output'])