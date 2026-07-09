# test_orchestrator.py
# Test the Orchestrator

from src.agents.orchestrator import Orchestrator
from src.core.memory import memory

print("=" * 60)
print("Testing Orchestrator")
print("=" * 60)

# Create the orchestrator
orchestrator = Orchestrator()
print(f"\n✅ Orchestrator created")
print(f"   Description: {orchestrator.description}")

# Test orchestration
print("\n--- Testing Orchestration ---")

goal = "Research AI customer service tools and write a competitive analysis report"
print(f"Goal: {goal}")

# Clear memory for fresh start
memory.start_task("orchestrator_test")

result = orchestrator.run(goal, max_steps=4)

print(f"\n--- Result ---")
print(f"Status: {result['status']}")

if result["status"] == "success":
    final_result = result.get("result")
    if isinstance(final_result, dict):
        print(f"Summary: {final_result.get('summary', 'No summary')}")

        # Check if a report was generated
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
