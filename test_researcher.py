# test_researcher.py
# Test the Researcher Agent

from src.agents.researcher import ResearcherAgent

print("=" * 60)
print("Testing Researcher Agent")
print("=" * 60)

# Create the agent
researcher = ResearcherAgent()
print(f"✅ Agent created: {researcher.name}")
print(f"   Description: {researcher.description}")

# Test research
print("\n--- Testing Research ---")

goal = "Research AI customer service tools in 2026"
print(f"Goal: {goal}")

result = researcher.run(goal, max_steps=5)

print(f"\n--- Result ---")
print(f"Status: {result['status']}")

if result["status"] == "success":
    # FIXED: Handle different result types
    final_result = result.get("result")

    if isinstance(final_result, dict):
        # If it's a dictionary, try to get the summary
        print(f"Summary: {final_result.get('summary', 'No summary available')}")

        # Show the full result structure for debugging
        print("\n--- Final Result Structure ---")
        for key, value in final_result.items():
            if key == "results" and isinstance(value, list):
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {value}")
    else:
        # If it's a string, just print it
        print(f"Result: {final_result}")

    # Show the steps taken
    if result.get("context"):
        print("\n--- Steps Taken ---")
        for i, step in enumerate(result["context"].steps_taken, 1):
            print(f"{i}. {step}")

    # Show any errors
    if result.get("context") and result["context"].errors:
        print("\n--- Errors ---")
        for error in result["context"].errors:
            print(f"  ⚠️ {error}")

else:
    print(f"Error: {result.get('error', 'Unknown error')}")

print("\n" + "=" * 60)
print("Test complete!")
