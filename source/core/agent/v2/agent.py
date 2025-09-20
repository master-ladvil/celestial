
from typing import List,Dict,Callable

from source.core.agent.v2.promptManager import PromptManager
from source.core.agent.v2.responseParser import ResponseParser
from source.core.agent.v2.toolDispatcher import ToolDispatcher
from source.util.logger import logger

class CelestialAgent:
    """Orchestrate thought-action-observation-loop"""
    def __init__(self,llm,tools: List[Callable]) -> None:
        self.llm = llm
        self.tools = tools
        self.prompt_manager = PromptManager()
        self.toolDispatcher =  ToolDispatcher(tools=tools)
        self.responseParser = ResponseParser()
        self.scratchpad: List[Dict[str, str]] = []
        logger.info("Celestial agent V2 is initialised with prompt and tool manager")

    def _reset_memory(self):
        self.scratchpad = []
        logger.debug("Scratchpad cleared")

    async def get_response(self,user_input) -> str:
        logger.info(f"Agent received input : {user_input}")
        self._reset_memory()
        max_loops=5

        for i in range(max_loops):
            prompt =  self.prompt_manager.build_prompt(
                user_input=user_input,
                tools=self.tools,
                scratchpad=self.scratchpad
            )

            logger.info(f"--- Thinking (Loop {i+1}) ----")
            raw_response = await self.llm.ainvoke(prompt)
            llm_output = raw_response.content
            logger.debug(f"LLM Raw Output:\n{llm_output}")

            parsed_response = self.responseParser.parse(llm_output)
            thought = parsed_response.get("thought","")
            if parsed_response["type"] == "final_answer":
                logger.info("Agent found the final answer.")
                return parsed_response["content"]

            if parsed_response["type"] == "action" :
                tool_name = parsed_response["action_name"]
                tool_input = parsed_response["action_input"]
                observation = self.toolDispatcher.execute_tool(tool_name=tool_name,tool_input=tool_input)
                logger.info(f"Observation from the tool : {observation}")

                self.scratchpad.append({
                    "thought" : thought,
                    "action_log": f"Action: {tool_name}\nAction Input: {tool_input}\nObservation: {observation}"
                })
                logger.debug("\n --- action scratchpad ---")
                logger.debug(self.scratchpad)
                logger.debug(" --- action scratchpad ---\n")

            else:
                logger.error("Agent failed to parse LLM Response")
                self.scratchpad.append({
                    "thought": thought,
                    "action_log": f"Invalid Response: My previous thought was invalid. I must think again, following the required format of 'Thought:', 'Action:' and 'Action Input:'."
                })

        logger.warning("Agent reached maximum loop limit.")
        return " I seem to be stuck in a thought loop.. Ill stop here to be safe"
