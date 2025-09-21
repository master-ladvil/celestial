import re
from typing import Dict
from source.util.logger import logger
class ResponseParser:
    def parse(self,response_text:str)-> Dict:

        thought_match =re.search(r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)", response_text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        final_answer_match = re.search(r"Final Answer:\s*(.*)", response_text, re.IGNORECASE | re.DOTALL)
        if final_answer_match:
            action_match = re.search(r"Action:\s*(.*?)",response_text,re.IGNORECASE | re.DOTALL)
            if action_match:
                logger.warning("LLM Hallucinated Final answer with Action...")
                return {"type": "FinalAnswerHallucination","Thought":thought}

            content = final_answer_match.group(1).strip()
            return {"type": "final_answer", "content": content, "thought": thought}

        action_match = re.search(r"Action:\s*(.*?)\nAction Input:\s*(.*?)(?:\n|$)", response_text, re.DOTALL)
        if action_match:

            if "\nObservation:" in action_match.group(0):
                logger.warning("LLM hallucinated an observation...")
                return {"type": "observationHallucination", "content": "LLM hallucinated an observation.", "thought": thought}

            action = action_match.group(1).strip()
            action_input = action_match.group(2).strip().strip('"')
            return {"type": "action", "action_name": action, "action_input": action_input, "thought": thought}

        if not final_answer_match and not action_match:
            logger.warning("LLM failed to provide  action or final answer.")
            return {"type": "noActionNoFinalAnswer","thought":thought}


        logger.warning(f"Could not parse LLM Response {response_text}")
        return {"type":"error","Contnet":"Could not process LLM Response"}