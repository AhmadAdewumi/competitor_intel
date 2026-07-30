from typing import Any, Dict
from unittest import result

from src.core.tool import BaseTool
from src.utils.logger import log


class CalculatorTool(BaseTool):
    """
    A tool that provides basic math operations
    (add, subtract, multiply, divide)
    """

    def __init__(self):
        super().__init__(
            name =  "calculator",
            description="performs basic maths operations:add, subtract, multiply, divide",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": "[add, subtract, multiply, divide]",
                        "description": "The math operation to perform",
                    },
                    "a":{
                        "type": "number",
                        "description": "First Number"
                    },
                    "b":{
                        "type": "number",
                        "description": "Second Number"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the calculator operation.

        Args:
            input_data: {
                "operation": "add" | "subtract" | "multiply" | "divide",
                "a": float,
                "b": float
            }

        Returns:
            {
                "success": bool,
                "result": float,
                "operation": str,
                "a": float,
                "b": float,
                "error": str (if failed)
            }
        """
        # Extract Input
        operation = input_data.get("operation")
        a = input_data.get("a")
        b =  input_data.get("b")

        #validate inputs
        if operation not in ["add", "subtract", "multiply", "divide"]:
            return {
                "success": False,
                "error": f"Invalid operation: {operation}. Must be one of: add, subtract, multiply, divide",
                "result": None
            }

        if not isinstance(a, (int, float)):
            return {
                "success": False,
                "error" : f"a must be a number, got {type(a)}",
                "result": None
            }

        if not isinstance(b, (int, float)):
            return {
                "success": False,
                "error" : f"b must be a number, got {type(b)}",
                "result": None
            }

        #perform the operation
        try:
            if operation == "add":
                result = a+b
            elif operation == "subtract":
                result = a -b
            elif operation == "multiply":
                result = a*b
            elif operation == "divide":
                if b == 0:
                    return {
                        "success":False,
                        "error": "Cannot divide by zero",
                        "result": None
                    }
                result = a/b

            else:
                return {
                    "success": False,
                    "error": "Unknown operation",
                    "result" : None
                }

            log.info(f"Calculator: {a} {operation} {b} = {result}")

            return {
                "success": True,
                "result": result,
                "operation": operation,
                "a": a,
                "b": b,
                "error": None
            }

        except Exception as e:
            log.error(f"Calculator error: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
