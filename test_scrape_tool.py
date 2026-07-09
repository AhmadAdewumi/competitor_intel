# test_scrape_tool.py
# Test the Scrape Tool

from src.tools.scrape import ScrapeTool
from src.core.tool import ToolRegistry

print("=" * 60)
print("Testing Scrape Tool")
print("=" * 60)

# Create the tool
scrape = ScrapeTool()
print(f"✅ Tool created: {scrape.name}")
print(f"   Description: {scrape.description}")

# Test scraping
print("\n--- Testing Scrape ---")

# Use a known good URL
test_url = "https://example.com"
print(f"Scraping: {test_url}")

result = scrape.run({"url": test_url, "max_chars": 1000})

if result["success"]:
    print(f"✅ Success!")
    print(f"   Title: {result['title']}")
    print(f"   Headings: {result['headings'][:3]}")
    print(f"   Content length: {result['char_count']} characters")
    print(f"\nContent preview:\n{result['content'][:300]}...")
else:
    print(f"❌ Failed: {result.get('error')}")

# Test with a real page
print("\n--- Testing with Real Page ---")
real_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
print(f"Scraping: {real_url}")

result = scrape.run({"url": real_url, "max_chars": 1500})

if result["success"]:
    print(f"✅ Success!")
    print(f"   Title: {result['title']}")
    print(f"   Headings: {result['headings'][:5]}")
    print(f"   Content length: {result['char_count']} characters")
    print(f"\nContent preview:\n{result['content'][:400]}...")
else:
    print(f"❌ Failed: {result.get('error')}")

# Test with registry
print("\n--- Testing with ToolRegistry ---")
registry = ToolRegistry()
registry.register(scrape)

schemas = registry.get_tool_schemas()
print(f"✅ Registry has {len(schemas)} tools")
print(f"\n{registry.list_tools()}")

print("\n" + "=" * 60)
print("Test complete!")