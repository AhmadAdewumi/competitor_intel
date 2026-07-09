# test_writer.py
# Test the Writer Agent

from src.agents.writer import WriterAgent
from src.core.memory import memory

print("=" * 60)
print("Testing Writer Agent")
print("=" * 60)

# First, make sure we have data in memory
print("\n--- Ensuring Data in Memory ---")
memory.start_task("test_writer")

# Add some data if needed
memories = memory.get_recent(10)
if len(memories) < 5:
    print("Adding sample data to memory...")
    memory.remember(
        "AI customer service tools include Zendesk, Intercom, and Freshdesk", "research"
    )
    memory.remember("Zendesk best for small businesses", "fact", {"source": "review"})
    memory.remember("Intercom excels at live chat", "fact", {"source": "review"})
    memory.remember("Freshdesk offers best free tier", "fact", {"source": "review"})
    memory.remember("Market expected to grow 25% in 2026", "research", {"source": "report"})

print(f"✅ {len(memory.get_recent(10))} memories available")

# Create the agent
writer = WriterAgent()
print(f"\n✅ Agent created: {writer.name}")
print(f"   Description: {writer.description}")

# Test writing
print("\n--- Testing Writing ---")

goal = "Write a competitive analysis report on AI customer service tools"
print(f"Goal: {goal}")

result = writer.run(goal, max_steps=4)

print(f"\n--- Result ---")
print(f"Status: {result['status']}")

if result["status"] == "success":
    final_result = result.get("result")
    if isinstance(final_result, dict):
        print(f"Summary: {final_result.get('summary', 'No summary')}")

        # Check if report was saved
        if final_result.get("filename"):
            print(f"Report saved: {final_result.get('filename')}")

        # Show the report preview
        report = final_result.get("report") or final_result.get("polished_report")
        if report:
            print(f"\n--- Report Preview ---")
            print(report[:500] + "..." if len(report) > 500 else report)
    else:
        print(f"Result: {final_result}")

    # Show steps
    if result.get("context"):
        print("\n--- Steps Taken ---")
        for i, step in enumerate(result["context"].steps_taken, 1):
            print(f"{i}. {step}")

else:
    print(f"Error: {result.get('error', 'Unknown error')}")

print("\n" + "=" * 60)
print("Test complete!")
