# test_orchestrator.py
import os
from src.agents.orchestrator import Orchestrator
from src.core.memory import memory

os.makedirs("reports", exist_ok=True)

print("=" * 60)
print("Testing Orchestrator (with step limit)")
print("=" * 60)

orchestrator = Orchestrator()
print(f"\n✅ Orchestrator created")

goal = "Research AI customer service tools and write a competitive analysis report"
print(f"Goal: {goal}")

memory.start_task("orchestrator_test")

print("\n⏳ Running agents... (should take 5-10 minutes)")
result = orchestrator.run(goal, max_steps=5)  # Changed from 20 to 5

print(f"\n--- Result ---")
print(f"Status: {result['status']}")

if result["status"] == "success":
    final_result = result.get('result', {})
    if isinstance(final_result, dict):
        if final_result.get("filename"):
            print(f"✅ Report saved: {final_result.get('filename')}")
            report_path = f"reports/{final_result.get('filename')}"
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    content = f.read()
                    print(f"\n--- Report Preview (first 500 chars) ---")
                    print(content[:500] + "..." if len(content) > 500 else content)
        elif final_result.get("summary"):
            print(f"Summary: {final_result.get('summary')}")

print("\n--- Steps Taken ---")
if result.get("context"):
    for i, step in enumerate(result["context"].steps_taken, 1):
        print(f"{i}. {step}")

print("\n--- Reports Directory ---")
reports = os.listdir("reports") if os.path.exists("reports") else []
if reports:
    for r in sorted(reports):
        size = os.path.getsize(f"reports/{r}")
        print(f"  📄 {r} ({size} bytes)")
else:
    print("  No reports found")

print("\n" + "=" * 60)