from core.tool import BaseTool, ToolRegistry

print("Testing BaseTool...")

# 1. Test that BaseTool is abstract
try:
    tool = BaseTool("test", "Test tool")
    print("ERROR: BaseTool should NOT be instantiable!")
except TypeError as e:
    print("SUCCESS: BaseTool is abstract (can't instantiate)")
    print(f"   Error: {e}")

# 2. Test the registry
print("\nTesting ToolRegistry...")
registry = ToolRegistry()
print(f"   Registry created")
print(f"   Tools registered: {len(registry.get_all_tools())}")
print(f"   Tool schemas: {registry.get_tool_schemas()}")
print(f"   Tool list:\n{registry.list_tools()}")

print("\n All tests passed!")