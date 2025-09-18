
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
        logger.info("Celestial agent V2 is initialised with prompt and tool manager")

    async def get_response(self,user_input) -> str:
        logger.info(f"Agent received input : {user_input}")
        scratchpad=""
        max_loops=5

        for i in range(max_loops):
            prompt =  self.prompt_manager.build_prompt(
                user_input=user_input,
                tools=self.tools,
                scratchpad=scratchpad
            )

            logger.info(f"--- Thinking (Loop {i+1}) ----")
            raw_response = await self.llm.ainvoke(prompt)
            llm_output = raw_response.content
            logger.debug(f"llm Output : {llm_output}")

            parsed_response = self.responseParser.parse(llm_output)
            if parsed_response["type"] == "final_answer":
                logger.info("Agent found the final answer.")
                return parsed_response["content"]

            if parsed_response["type"] == "action" :
                tool_name = parsed_response["action_name"]
                tool_input = parsed_response["action_input"]
                observation = self.toolDispatcher.execute_tool(tool_name=tool_name,tool_input=tool_input)
                logger.info(f"Observation from the tool : {observation}")
                scratchpad += f"\n{llm_output}\nObservation: {observation}"

                logger.debug("\n --- scratchpad ---")
                logger.debug(scratchpad)
                logger.debug("-------------\n")

            else:
                logger.error("Agent failed to parse LLM Response")
                return "Im sorry, i got a bit confused. could you please rephrase your request?"

        logger.warning("Agent reached maximum loop limit.")
        return " I seem to be stuck in a thought loop.. Ill stop here to be safe"
