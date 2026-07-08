from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from openai.types.responses import tool

from utils.logger import log


class BaseTool(ABC):
    """
    - defines what every tool must implement
    - every subclasss must implement the runmethod
    - all tools use this same run method

    1. agents get a list of available tools
    2. agents selects a tool to use
    3. agent callsl tools.run(input_data
    4. tools return a consistent result

    # ------ how it really works-----------
    1. agent gets a goal
    2. agents asks ToolRegistry: what tool can I use?
    3. Agent plans: I need to search first
    4. Tool returns result
    5. Agent reflects and continues

    TOOL REGISTRY --> (SEARCH TOOL. CALCULATOR TOOL.  SCRAPE TOOL)
    """

    def __init__(self, name: str, description: str, parameters: Dict[str, Any] = None):
        """
        :param name:
        :param description:
        :param parameters:
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        log.info(f"Tool '{name}' initialized")

    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
         Execute the tool with the given input.

        tools use THIS method. Agents call it consistently.

        Args:
            input_data: The input for the tool (keys match the parameters schema)

        Returns:
            Dict with at least:
                - "success": bool (True if successful)
                - "result": Any (the actual result)
                - "error": str (if success is False)
        """

        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        validate that the input matche sthe parameter sche,ma
         Prevents errors from invalid inputs.
        Checks that all required parameters are present.

        :param input_date:
        :return:
        """

        if not self.parameters:
            return True

        required = self.parameters.get("required", [])
        for param in required:
            if param not in input_data:
                log.warning(f"Tool '{self.name}' missing required parameter: {param}")
                return False

        properties = self.parameters.get("property", {})
        for param, value in input_data.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type == "number" and not isinstance(value, (int, float)):
                    log.warning(
                        f"Tool '{self.name}' parameter '{param}' should be number, got {type(value)}"
                    )
                    return False
                if expected_type == "string" and not isinstance(value, str):
                    log.warning(
                        f"Tool '{self.name}' parameter '{param}' should be string, got {type(value)}"
                    )
                    return False
                if expected_type == "boolean" and not isinstance(value, bool):
                    log.warning(
                        f"Tool '{self.name}' parameter '{param}' should be boolean, got {type(value)}"
                    )
                    return False
        return True

    def get_schema(self) -> Dict[str, Any]:
        """
        get the tool's schema (name, description, parameters

        why: coz the agent needs  to know what tools are availabel and how to use them
        :return: dict with name, description and parameters
        """
        return {"name": self.name, "description": self.description, "parameters": self.parameters}


class ToolRegistry:
    """
    A registry for all available tools

    coz agents needs to knoe the tools they have access to
    how does it work: tools registers themselves and agents can list them
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        log.info("ToolRegistry initialized")

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        log.info(f"registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """
        -- get all registered tools
        :return: list of all tools
        """
        return list(self._tools.values())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Ge the schema of all registered tools coz agents need to know the tools available
        :return: schema of all registered tools
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def list_tools(self):
        """
        human-readable list of available tools (for debugging and agent prompt)
        :return:
        """
        if not self._tools:
            return "No tools available"

        result = "Available tools \n"
        for tool in self._tools.values():
            result += f"  - {tool.name}: {tool.description}\n"
        return result
