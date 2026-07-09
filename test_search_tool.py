# test_search_tool.py
# Test the Search Tool

import os
from src.tools.search import SearchTool
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("=" * 60)
print("Testing Search Tool")
print("=" * 60)

# Check if API key is set
api_key = os.getenv("TAVILY_API_KEY")
if not api_key:
    print(" TAVILY_API_KEY not found in .env")
    print("   Please add it: TAVILY_API_KEY=tvly-...")
    print("   Get one at: https://tavily.com")
    exit(1)

print("✅ API key found")

# Create the tool
search = SearchTool()
print(f"✅ Tool created: {search.name}")
print(f"   Description: {search.description}")

# Test search
print("\n--- Testing Search ---")

test_query = "AI customer service tools 2026"
print(f"Searching: '{test_query}'")

result = search.run({"query": test_query, "max_results": 3})

if result["success"]:
    print(f"✅ Found {result['count']} results")
    print("\nResults:")
    for i, item in enumerate(result["results"], 1):
        print(f"\n{i}. {item.get('title', 'No title')}")
        print(f"   URL: {item.get('url', 'No URL')}")
        print(f"   Snippet: {item.get('content', 'No snippet')[:150]}...")
else:
    print(f"❌ Search failed: {result.get('error')}")

# Test with registry
print("\n--- Testing with ToolRegistry ---")
from src.core.tool import ToolRegistry

registry = ToolRegistry()
registry.register(search)
print(f"✅ Registry has {len(registry.get_all_tools())} tools")
print(f"\n{registry.list_tools()}")

print("\n" + "=" * 60)
print("Test complete!")