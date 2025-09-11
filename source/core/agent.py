# source/core/agent.py

class CelestialAgent:

    """ The core agent that orchestrate the thought-action-observation loop"""

    def __init(self,llm,tools):
        self.llm=llm
        self.tools=tools
        print("Celestial agent initialized")

    async def get_response(self, user_input: str) -> str:

        print(f"Agent received input {user_input}")
        raw_response = await self.llm.ainvoke(user_input)
        return raw_response.content
