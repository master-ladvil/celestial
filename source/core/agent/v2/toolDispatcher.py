from typing import Callable,List,Dict


class ToolDispatcher:
    def __init__(self,tools:List[Callable]):
        self.tools : Dict[str,Callable] = {tool.name:tool for tool in tools}

    def execute_tool(self,tool_name:str,tool_input:str)-> str:
        """
        executes a tool by its name with given input
        :param tool_name: name of the tool
        :param tool_input: input for the tool
        :return: output from tool as a string or error message
        """

        if tool_name not in self.tools:
            return f"Error : Tool '{tool_name}' not found. Available tools : {list(self.tools.keys())}"

        tool_function = self.tools[tool_name]
        try:
            if tool_input in (None,""):
                return tool_function()
            else:
                return tool_function(tool_input)
        except Exception as e:
            return f"Error while running the tool {tool_name} : {e}"