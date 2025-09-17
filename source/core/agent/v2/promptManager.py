import os
import re
from typing import Callable,List


class PromptManager:

    def __init__(self,prompt_file:str = "config/main/prompt.txt"):
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) #go up one level from core
        self.prompt_template_path = os.path.join(script_dir,prompt_file)
        if not os.path.exists(self.prompt_template_path):
            raise FileNotFoundError(f"Prompt file cannot be found at the location : {self.prompt_template_path}")
        with open(self.prompt_template_path,'r') as f:
            self.template = f.read()

    def _format_tools(self,tools:List[Callable])->str:
        """Format the list of tools into a string description"""
        return "\n".join([f"-{tool.name}:{tool.description}" for tool in tools])

    def build_prompt(self,user_input:str,tools:List[Callable],scratchpad:str)->str:
        """builds the prompt by replacing the keys in the prompt with the values"""
        tool_names = ", ".join([tool.name for tool in tools])
        tool_description = self._format_tools(tools)

        prompt = self.template.format(
            tools=tool_description,
            tool_names=tool_names,
            input=user_input,
            agent_scratchpad=scratchpad
        )

        return prompt
