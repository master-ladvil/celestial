import re
from typing import Dict
from source.util.logger import logger
class ResponseParser:
    def parse(self,response_text:str)-> Dict:
        final_answer_match = re.search(r"Final Answer:\s*(.*)", response_text, re.IGNORECASE | re.DOTALL)
        if final_answer_match:
            content = final_answer_match.group(1).strip()
            return {"type": "final_answer", "content": content}

        pattern = re.compile(r"Thought:\s*(.*?)\nAction:\s*(.*?)\nAction Input:\s*(.*)", re.DOTALL)
        action_match = pattern.search(response_text)
        if action_match:
            action_input = action_match.group(3).strip().strip('"')

            if "\nObservation:" in action_match.group(0):
                logger.warning(f"LLM hallucinated an observation... removing hallucinated observation")
                action_input=action_input.split("\nObservation")[0]

            thought = action_match.group(1).strip()
            action = action_match.group(2).strip()


            return {"type" : "action","thought" : thought,"action_name":action,"action_input":action_input}

        logger.warning(f"Could not parse LLM Response {response_text}")
        return {"type":"error","Contnet":"Could not process LLM Response"}