from core.agent import BaseAgent
from core.tool import BaseTool, ToolRegistry

try:
    agent = BaseAgent("Test agent", "Just a test agent")
    print("ERROR: Base agent should not be instantiable")

except TypeError as e:
    print("SUCCESS: Base Agent is abstract, can't instantiate")
    print(f" Error: {e}")