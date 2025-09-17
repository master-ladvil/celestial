
from typing import List,Dict,Callable

from source.core.agent.v2.promptManager import PromptManager
from source.core.agent.v2.toolDispatcher import ToolDispatcher


class CelestialAgent:
    """Orchestrate thought-action-observation-loop"""
    def __init__(self,llm,tools: List[Callable]) -> str:
        self.llm = llm
        self.tools = tools
        self.prompt_manager = PromptManager()
        self.toolDispatcher =  ToolDispatcher(tools=tools)
        print("Celestial agent V2 is initialised with prompt and tool manager")

    async def get_response(self,user_input) -> str:
        print(f"Agent received input : {user_input}")

        prompt = self.prompt_manager.build_prompt(user_input=user_input,tools=self.tools,scratchpad="")
        print("--- BUILT PROMPT ---")
        print(prompt)
        print("--------------------")

        raw_response = await self.llm.ainvoke(prompt)
        return raw_response.content