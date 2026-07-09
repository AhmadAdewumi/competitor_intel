# test_calculator_tool.py
# Test the Calculator Tool

from src.tools.calculator import CalculatorTool
from src.core.tool import ToolRegistry

print("=" * 60)
print("Testing Calculator Tool")
print("=" * 60)

# 1. Create the tool
calculator = CalculatorTool()
print(f"✅ Tool created: {calculator.name}")
print(f"   Description: {calculator.description}")
print(f"   Parameters: {calculator.parameters}")

# 2. Test operations
print("\n--- Testing Operations ---")

test_cases = [
    {"operation": "add", "a": 5, "b": 3, "expected": 8},
    {"operation": "subtract", "a": 10, "b": 4, "expected": 6},
    {"operation": "multiply", "a": 6, "b": 7, "expected": 42},
    {"operation": "divide", "a": 15, "b": 3, "expected": 5},
]

for test in test_cases:
    result = calculator.run(test)
    if result["success"]:
        print(f"✅ {test['a']} {test['operation']} {test['b']} = {result['result']} (expected: {test['expected']})")
    else:
        print(f"❌ Error: {result['error']}")

# 3. Test error cases
print("\n--- Testing Error Cases ---")

# Division by zero
result = calculator.run({"operation": "divide", "a": 10, "b": 0})
if not result["success"]:
    print(f"✅ Division by zero caught: {result['error']}")

# Invalid operation
result = calculator.run({"operation": "power", "a": 2, "b": 3})
if not result["success"]:
    print(f"✅ Invalid operation caught: {result['error']}")

# Invalid type for 'a'
result = calculator.run({"operation": "add", "a": "five", "b": 3})
if not result["success"]:
    print(f"✅ Invalid type caught: {result['error']}")

# 4. Test with registry
print("\n--- Testing with ToolRegistry ---")
registry = ToolRegistry()
registry.register(calculator)

schemas = registry.get_tool_schemas()
print(f"✅ Registry has {len(schemas)} tool")
print(f"   Tool schema: {schemas[0]}")

tool_list = registry.list_tools()
print(f"\n{tool_list}")

print("\n" + "=" * 60)
print("All tests passed!")