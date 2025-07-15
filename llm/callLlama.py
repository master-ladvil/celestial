from idlelib.history import History

from ollama import chat
from pathlib import Path
import json

class CallLlama:

    HISTORY_PATH = Path("chat_history.json")
    MODEL_NAME = "llama3-gradient"

    def  __init__(self, model):
        self.MODEL_NAME = model

    def askLlama(self,prompt:str)-> str:
        history = self.__loadHistory()
        history.append({"role" : "user","content" : prompt})

        response = chat(
            model = self.MODEL_NAME,
            messages=history
        )

        replyHistory = {"role": "assistant", "content" : response.message.content}
        history.append(replyHistory)
        self.__saveHistory(history)

        return response.message.content

    def __loadHistory(self) -> list[dict]:
       if self.HISTORY_PATH.exists():
           text = self.HISTORY_PATH.read_text()
           if not text.strip():
               return []
           try:
               return json.loads(text)
           except json.JSONDecodeError:
               #TODO :  clear file and start new
               return []

       return []

    def __saveHistory(self, history : list[dict]):
        self.HISTORY_PATH.write_text(json.dumps(history, indent=2))

    def setModelName(self,model : str):
        self.MODEL_NAME = model

    def setHistoryPath(self,path : str):
        self.HISTORY_PATH = Path(path)