
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
        self.scratchpad = ""
        logger.info("Celestial agent V2 is initialised with prompt and tool manager")

    def _reset_memory(self):
        self.scratchpad = ""
        logger.debug("Scratchpad cleared")

    def _print_scratchpad(self):
        logger.debug("\n --- action scratchpad ---\n")
        logger.debug(self.scratchpad)
        logger.debug(" \n--- action scratchpad ends---\n")

    async def get_response(self,user_input) -> str:
        logger.info(f"Agent received input : {user_input}")
        self._reset_memory()
        max_loops=8
        for i in range(max_loops):
            self.scratchpad += f"\nIteration : {i}\n"
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

                self.scratchpad += f"\nThought: {thought}\nAction: {tool_name}\nAction Input: {tool_input}\nObservation: {observation}"
                if i> 2:
                    self.scratchpad +="\n I received the observation from the tool,I also has previous observations from my previous actions, i should check all the observations and give the Thought to check if the user request is completed to give the Final Answer or should i take another action"
                else:
                    self.scratchpad +="\n I received the observation from the tool, i will now give the thought of using this observation to give the final answer or take another action"
                self._print_scratchpad()

            elif parsed_response["type"] == "observationHallucination":
                self.scratchpad += f"\n Invalid Response: In my previous response i gave the 'Observation' which must be given by the tool. I must think again, and should only give 'Thought:', 'Action:' and 'Action Input: in my next iteration'."
                self._print_scratchpad()
            elif parsed_response["type"] == "FinalAnswerHallucination":
                self.scratchpad += f"\n Invalid Response: In my previous response i gave the action as well as Final answer. I should not give final answer or observation with Action. The observation will be provided by the tool, i should wait for the observation and then analyse the observation to give the final answer."
                self._print_scratchpad()

            elif parsed_response["type"] == "noActionNoFinalAnswer":
                self.scratchpad += f"thought: {thought}\n Invalid Response: My previous thought did not have an action or final answer after a thought. I must think if i should give a final answer or an action and action input"
                self._print_scratchpad()

            else:
                logger.error("Agent failed to parse LLM Response")
                self.scratchpad += f"thought: {thought}\n Invalid Response: My previous thought was invalid. I must think again, following the required format of 'Thought:', 'Action:' and 'Action Input:'."
                self._print_scratchpad()

        logger.warning("Agent reached maximum loop limit.")
        return " I seem to be stuck in a thought loop.. Ill stop here to be safe"
