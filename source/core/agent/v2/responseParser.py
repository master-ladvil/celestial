import re
from typing import Dict
from source.util.logger import logger
class ResponseParser:
    def parse(self,response_text:str)-> Dict:
        if "Final Answer" in response_text:
            return {"type":"final_answer","content": response_text.split("Final Answer:")[-1].strip()}

        action_match = re.search(r"Action:\s*(.*?)\nAction Input:\s*(.*)", response_text, re.DOTALL)
        if action_match :
            action = action_match.group(1).strip()
            action_input = action_match.group(2).strip().strip('"')
            return {"type" : "action","action_name":action,"action_input":action_input}

        logger.warning(f"Could not parse LLM Response {response_text}")
        return {"type":"error","Contnet":"Could not process LLM Response"}