# src/agents/writer.py
# COMPETITORINTEL - Writer Agent
#
# Write professional reports from researched data.
# So that Raw data and analysis need to be presented clearly.
# It reads memory and writes structured reports.
# ============================================
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.agent import BaseAgent
from src.core.memory import memory
from src.utils.logger import log
from src.utils.trace import publish_trace


class WriterAgent(BaseAgent):
    """
    An agent that writes professional reports from researched data.

    How it works:
    1. Reads all research and analysis from memory
    2. Synthesizes everything into a coherent narrative
    3. Writes a structured report
    4. Saves the report to a file
    """

    def __init__(self):
        super().__init__(
            name="Writer",
            description="Writes professional reports from researched data and analysis.",
        )

        log.info("Writer Agent initialized")

    def plan(self, goal: str) -> List[str]:
        """
        Break down the writing goal into steps.
        Instead of relying on the LLM (which is unpredictable and can generate 11+ steps),
        we enforce a strict, deterministic 4-step workflow to guarantee completion.
        """
        log.info(f"Writer planning for: {goal}")

        # Hardcoded deterministic steps guarantee we never hit the max_steps limit
        # and guarantee that the report is ALWAYS saved at the end.
        steps = [
            "Review research and analysis from memory",
            "Organize information into a report outline",
            "Write the comprehensive professional report",
            "Save the final report to a file"
        ]

        log.info(f"Planned {len(steps)} steps")
        return steps

    def execute_step(self, step: str) -> Dict[str, Any]:
        """
        Execute a single step in the writing plan.
        """
        log.info(f"Executing step: {step}")
        step_lower = step.lower()

        # Step 1: Review memory
        if "review" in step_lower or "memory" in step_lower:
            return self._execute_review(step)

        # Step 2: Organize
        elif "organize" in step_lower or "outline" in step_lower:
            return self._execute_organize(step)

        # Step 3: Write
        elif "write" in step_lower or "report" in step_lower:
            return self._execute_write(step)

        # Step 4: Save
        elif "save" in step_lower or "file" in step_lower:
            return self._execute_save(step)

        # Default: Use LLM
        else:
            return self._execute_general(step)

    def _execute_review(self, step: str) -> Dict[str, Any]:
        """
        Review all research and analysis from memory.
        """
        # Get all memories
        all_memories = memory.get_recent(limit=50)

        if not all_memories:
            # HANDLE EMPTY MEMORY
            log.warning("No memories found! Agents aren't saving data.")
            return {
                "summary": "No data available. The researcher and analyst agents need to save data first.",
                "error": "No data in memory",
                "content": "No research data available to write a report. Please run the Researcher and Analyst agents first.",
            }

        # Categorize memories
        facts = [m for m in all_memories if m.type == "fact"]
        research = [m for m in all_memories if m.type == "research"]
        insights = [m for m in all_memories if m.type == "insight"]

        # Format for review
        memory_text = "Research findings:\n"
        for r in research[:15]:
            memory_text += f"- {r.content}\n"

        memory_text += "\nKey facts:\n"
        for f in facts[:15]:
            memory_text += f"- {f.content}\n"

        memory_text += "\nInsights:\n"
        for i in insights[:15]:
            memory_text += f"- {i.content}\n"

        if not memory_text:
            memory_text = "No memories found"

        return {
            "summary": f"Reviewed {len(all_memories)} memories",
            "facts_count": len(facts),
            "research_count": len(research),
            "insights_count": len(insights),
            "content": memory_text,
        }

    def _execute_organize(self, step: str) -> Dict[str, Any]:
        """
        Organize information into report sections.
        """
        # Get the review content
        review = self._get_last_review()

        if not review:
            return {"summary": "No content to organize", "error": "No review found"}

        # Using LLM to organize
        system_prompt = """You are a report organizer. Create a clear outline for a professional competitive intelligence report.

        The report MUST include:
        1. Executive Summary
        2. Market Overview
        3. Major Players & Competitors
        4. Detailed Analysis (Strengths, Weaknesses, Trends)
        5. Conclusions & Future Outlook

        Provide a detailed outline with bullet points for each section."""

        user_prompt = f"Content to organize:\n{review[:3000]}\n\nCreate a report outline based ONLY on this provided data."

        response = self.ask_llm(system_prompt, user_prompt)

        return {"summary": "Report outline created", "outline": response}

    def _execute_write(self, step: str) -> Dict[str, Any]:
        """
        Write the report.
        """
        publish_trace("Writer", "Drafting the full comprehensive report...")

        # Get the outline
        outline = self._get_last_outline()
        review = self._get_last_review()

        if not outline and not review:
            return {"summary": "No content to write", "error": "No outline or review found"}

        # Use LLM to write the report
        system_prompt = """You are a professional report writer. Write a comprehensive, well-structured report.

        The report MUST:
        1. Be written in a professional, formal, business-friendly tone.
        2. Use clear markdown formatting (H1, H2, H3, bullet points, bold text).
        3. Be evidence-based, utilizing only the provided research data.
        4. Flow logically from the Executive Summary to the Conclusion.
        5. Be highly detailed and thorough. Do not summarize too briefly.

        Write the COMPLETE report in one single response."""

        user_prompt = f"""Write a professional report based on this information:

        Outline:
        {outline if outline else "Use a standard report structure"}

        Data/Research Content:
        {review[:4000] if review else "No additional content provided"}

        Write the complete report now."""

        response = self.ask_llm(system_prompt, user_prompt)

        publish_trace("Writer", "Report written", f"{len(response)} characters generated.")

        return {"summary": "Report written", "report": response}

    def _execute_save(self, step: str) -> Dict[str, Any]:
        """
        Save the report to a file.
        """
        # Get the report
        report = self._get_last_report()

        if not report:
            return {"summary": "No report to save", "error": "No report found"}

        # Save to file
        os.makedirs("reports", exist_ok=True)
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = f"reports/{filename}"

        with open(filepath, "w") as f:
            f.write(report)

        log.info(f"✅ Report saved to {filepath}")

        # Also save to memory
        memory.remember(
            content=f"Report written: {filename}",
            entry_type="report",
            metadata={"filename": filename, "filepath": filepath},
            tags=["report", "output"],
        )

        # Return BOTH the summary AND the report (vital for the Orchestrator)
        return {
            "summary": f"Report saved to {filename}",
            "filename": filename,
            "filepath": filepath,
            "report": report,
            "polished_report": report,
        }

    def _execute_general(self, step: str) -> Dict[str, Any]:
        """
        Handle general steps using the LLM.
        """
        # Get context from memory
        context = memory.recall(limit=5)

        system_prompt = "You are a helpful writing assistant. Handle the given task."
        user_prompt = f"Context:\n{context}\n\nTask: {step}\n\nProvide a detailed response."

        response = self.ask_llm(system_prompt, user_prompt)

        return {"summary": f"Completed: {step[:50]}...", "response": response}

    def _get_last_review(self) -> Optional[str]:
        """Get the last review from context."""
        if not self.context:
            return None

        for result in reversed(self.context.results):
            if isinstance(result, dict) and result.get("content"):
                return result["content"]
        return None

    def _get_last_outline(self) -> Optional[str]:
        """Get the last outline from context."""
        if not self.context:
            return None

        for result in reversed(self.context.results):
            if isinstance(result, dict) and result.get("outline"):
                return result["outline"]
        return None

    def _get_last_report(self) -> Optional[str]:
        """Get the last report from context."""
        if not self.context:
            return None

        for result in reversed(self.context.results):
            if isinstance(result, dict) and result.get("report"):
                return result["report"]
        return None

    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect on the result and decide next steps.
        """
        log.info("Writer reflecting on step result...")

        if result.get("error"):
            return {"should_stop": False, "reason": "Error occurred but continuing"}

        # We are using a 4-step hardcoded process. We stop when we reach step 4.
        if self.context and self.context.current_step >= 4:
            return {"should_stop": True, "reason": "Report complete and saved"}

        return {"should_stop": False, "reason": "Continuing writing"}