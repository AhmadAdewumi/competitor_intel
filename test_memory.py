# test_memory.py
# Test the Memory System

from src.core.memory import MemorySystem

print("=" * 60)
print("Testing Memory System")
print("=" * 60)

# Create memory system
memory = MemorySystem()
print("✅ Memory system created")

# Test short-term memory
print("\n--- Testing Short-Term Memory ---")
memory.start_task("test_task_1")
memory.remember("My name is Ahmad", "conversation", {"speaker": "user"})
memory.remember("I'm researching AI tools", "conversation", {"speaker": "user"})
memory.remember("Found 3 AI tools: Tool A, Tool B, Tool C", "research")

# Recall short-term
print("\nShort-term recall:")
context = memory.recall(limit=3)
print(context)

# Test long-term memory
print("\n--- Testing Long-Term Memory ---")
memory.remember("Zendesk is best for small businesses", "fact", {"source": "website"}, ["zendesk", "pricing"])
memory.remember("Intercom excels at live chat", "fact", {"source": "website"}, ["intercom", "features"])
memory.remember("Freshdesk offers the best free tier", "fact", {"source": "website"}, ["freshdesk", "pricing"])

# Search long-term
print("\nLong-term search:")
results = memory.long_term.search_by_tags(["pricing"])
for r in results:
    print(f"  - {r.content}")

# Get context
print("\n--- Full Context ---")
context = memory.recall("AI tools", limit=5)
print(context)

# Test persistence
print("\n--- Testing Persistence ---")
print("Memory saved to memory.json")
print("Restart the script to verify it persists")

print("\n" + "=" * 60)
print("Test complete!")