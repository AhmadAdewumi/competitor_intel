# test_analyst.py
# Test the Analyst Agent

from src.agents.analyst import AnalystAgent
from src.core.memory import memory

print("=" * 60)
print("Testing Analyst Agent")
print("=" * 60)

# First, add some data to memory
print("\n--- Adding Data to Memory ---")
memory.start_task("test_analyst")
memory.remember(
    "Zendesk is best for small businesses (under 50 employees)",
    "fact",
    {"source": "website"},
    ["zendesk", "smb"],
)
memory.remember(
    "Intercom excels at live chat and messaging",
    "fact",
    {"source": "website"},
    ["intercom", "features"],
)
memory.remember(
    "Freshdesk offers the best free tier and SMB pricing",
    "fact",
    {"source": "website"},
    ["freshdesk", "pricing"],
)
memory.remember(
    "All three tools offer AI chatbot capabilities",
    "research",
    {"source": "analysis"},
    ["ai", "chatbot"],
)
memory.remember(
    "Zendesk and Intercom target enterprise, Freshdesk targets SMBs",
    "research",
    {"source": "analysis"},
    ["segmentation"],
)
memory.remember(
    "AI customer service market expected to grow 25% in 2026",
    "research",
    {"source": "industry report"},
    ["market", "growth"],
)

print("✅ Added 6 facts to memory")

# Create the agent
analyst = AnalystAgent()
print(f"\n✅ Agent created: {analyst.name}")
print(f"   Description: {analyst.description}")

# Test analysis
print("\n--- Testing Analysis ---")

goal = "Analyze the AI customer service tool market"
print(f"Goal: {goal}")

result = analyst.run(goal, max_steps=10)

print(f"\n--- Result ---")
print(f"Status: {result['status']}")

if result["status"] == "success":
    final_result = result.get("result")
    if isinstance(final_result, dict):
        print(f"Summary: {final_result.get('summary', 'No summary')}")
        print(
            f"Steps taken: {len(result.get('context', {}).steps_taken if result.get('context') else [])}"
        )
    else:
        print(f"Result: {final_result}")

    # Show steps
    if result.get("context"):
        print("\n--- Steps Taken ---")
        for i, step in enumerate(result["context"].steps_taken, 1):
            print(f"{i}. {step}")

    # Show if analysis was saved to memory
    print("\n--- Memory Check ---")
    recent = memory.get_recent(5)
    for mem in recent:
        print(f"  [{mem.type}] {mem.content[:100]}...")

else:
    print(f"Error: {result.get('error', 'Unknown error')}")

print("\n" + "=" * 60)
print("Test complete!")
