# src/agents/analyst.py
# Analyst Agent
import os

# : Analyze researched data and draw conclusions.
# Raw data is useless without analysis, Reads memory, analyzes patterns, saves insights.
# ============================================
from typing import Any, Dict, List, Optional

from src.core.agent import BaseAgent
from src.core.memory import memory
from src.tools.calculator import CalculatorTool
from src.utils.logger import log


class AnalystAgent(BaseAgent):
    """
    An agent that analyzes researched data and draws conclusions.

    How it works:
    1. Reads recent research from memory
    2. Analyzes patterns and trends
    3. Draws conclusions
    4. Saves insights back to memory
    """

    def __init__(self):
        super().__init__(
            name="Analyst",
            description="Analyzes researched data, finds patterns, and draws conclusions.",
        )

        self.calculator_tool = CalculatorTool()
        log.info("Analyst Agent initialized")

    def plan(self, goal: str) -> List[str]:
        """
        Break down the analysis goal into steps.
        """
        log.info(f"Analyst planning for: {goal}")

        # Using the LLM to plan
        system_prompt = """You are an analysis planner. Break down the analysis goal into specific steps.

        For analysis tasks, typical steps are:
        1. Review existing research and data
        2. Identify patterns and trends
        3. Compare and contrast findings
        4. Draw conclusions and insights

        Return a list of steps (one per line).
        Be specific about what to analyze."""

        user_prompt = f"Analysis goal: {goal}\n\nBreak this down into specific steps."

        response = self.ask_llm(system_prompt, user_prompt)

        # Parse the response into steps
        steps = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove numbering like "1. " or "- "
                clean_line = line
                if line[0].isdigit() and ". " in line:
                    clean_line = line.split(". ", 1)[1] if ". " in line else line
                elif line.startswith("- "):
                    clean_line = line[2:]
                elif line.startswith("* "):
                    clean_line = line[2:]

                if clean_line:
                    steps.append(clean_line)

        # If no steps were parsed, use default steps
        if not steps:
            steps = [
                f"Review research about: {goal}",
                "Identify patterns and trends",
                "Compare different findings",
                "Draw conclusions and insights",
                "Save analysis to memory",
            ]

        log.info(f"Planned {len(steps)} steps")
        return steps

    def execute_step(self, step: str) -> Dict[str, Any]:
        """
        Execute a single step in the analysis plan.
        """
        log.info(f"Executing step: {step}")
        step_lower = step.lower()

        # Step 1: Review research
        if "review" in step_lower or "research" in step_lower or "memory" in step_lower:
            return self._execute_review(step)

        # Step 2: Identify patterns
        elif "pattern" in step_lower or "trend" in step_lower:
            return self._execute_patterns(step)

        # Step 3: Compare
        elif "compare" in step_lower or "contrast" in step_lower:
            return self._execute_compare(step)

        # Step 4: Conclude
        elif "conclusion" in step_lower or "insight" in step_lower:
            return self._execute_conclude(step)

        # Step 5: Save to memory
        elif "save" in step_lower or "memory" in step_lower:
            return self._execute_save(step)

        # Default: Use LLM
        else:
            return self._execute_general(step)

    def _execute_review(self, step: str) -> Dict[str, Any]:
        """
        Review existing research from memory.
        """
        # Get relevant memories
        memories = memory.get_recent(limit=10)

        # Also search for context
        context_memories = memory.recall(self.context.goal if self.context else "", limit=5)

        # Format the memories
        memory_text = ""
        for mem in memories:
            memory_text += f"- [{mem.type}] {mem.content}\n"

        if memory_text:
            memory_text = "Recent memories:\n" + memory_text

        # Use LLM to summarize the research
        system_prompt = """You are a research analyst. Review the provided research findings.

        Identify:
        1. Key findings
        2. Important data points
        3. Gaps in the research

        Provide a clear review."""

        user_prompt = f"Task: {step}\n\n{memory_text}\n\nProvide a review of these findings."

        response = self.ask_llm(system_prompt, user_prompt)

        return {
            "summary": "Research reviewed",
            "review": response,
            "memories_reviewed": len(memories),
            "gaps": "No obvious gaps identified",
        }

    def _execute_patterns(self, step: str) -> Dict[str, Any]:
        """
        Identify patterns and trends in the data.
        """
        # Get all memories
        memories = memory.get_recent(limit=20)

        if not memories:
            return {"summary": "No memories to analyze for patterns", "error": "No data available"}

        # Format memories
        memory_text = ""
        for mem in memories:
            memory_text += f"- [{mem.type}] {mem.content}\n"

        # Use LLM to find patterns
        system_prompt = """You are a data analyst. Find patterns and trends in the provided data.

        Look for:
        1. Common themes
        2. Recurring topics
        3. Emerging trends
        4. Anomalies or outliers

        Be specific about what you find."""

        user_prompt = f"Task: {step}\n\nData:\n{memory_text}\n\nIdentify patterns and trends."

        response = self.ask_llm(system_prompt, user_prompt)

        return {
            "summary": "Patterns identified",
            "patterns": response,
            "data_points": len(memories),
        }

    def _execute_compare(self, step: str) -> Dict[str, Any]:
        """
        Compare different findings.
        """
        # Get memories by type
        fact_memories = memory.long_term.search_by_type("fact", limit=10)
        research_memories = memory.long_term.search_by_type("research", limit=10)

        if not fact_memories and not research_memories:
            return {"summary": "No data available to compare", "error": "No data found"}

        # Format
        facts_text = "\n".join([f"- {m.content}" for m in fact_memories[:5]])
        research_text = "\n".join([f"- {m.content}" for m in research_memories[:5]])

        # Use LLM to compare
        system_prompt = """You are a comparative analyst. Compare and contrast the provided findings.

        Identify:
        1. Similarities
        2. Differences
        3. Contradictions
        4. Unique findings

        Provide a clear comparison."""

        user_prompt = f"""Task: {step}

Facts:
{facts_text}

Research:
{research_text}

Compare these findings."""

        response = self.ask_llm(system_prompt, user_prompt)

        return {
            "summary": "Comparison completed",
            "comparison": response,
            "facts_analyzed": len(fact_memories),
            "research_analyzed": len(research_memories),
        }

    def _execute_conclude(self, step: str) -> Dict[str, Any]:
        """
        Draw conclusions and insights.
        """
        from src.utils.trace import publish_trace

        # Debug: check if run_id exists
        run_id = os.environ.get("CURRENT_RUN_ID")
        log.info(f"Trace debug: CURRENT_RUN_ID = {run_id}")

        publish_trace("Analyst", "Drawing conclusions and insights...")

        # Get recent analysis from context
        patterns = self._get_last_patterns()
        comparison = self._get_last_comparison()

        # Use LLM to draw conclusions
        system_prompt = """You are a conclusion expert. Draw clear, actionable conclusions from the provided analysis.

        Your conclusions should be:
        1. Evidence-based
        2. Specific
        3. Actionable
        4. Forward-looking

        Provide a clear set of conclusions."""

        user_prompt = f"""Task: {step}

    Patterns identified:
    {patterns if patterns else "No patterns identified"}

    Comparison:
    {comparison if comparison else "No comparison available"}

    Draw conclusions and insights."""

        response = self.ask_llm(system_prompt, user_prompt)

        publish_trace("Analyst", "Conclusions drawn", response[:200])

        memory.remember(
            content=f"Analysis conclusion: {response[:500]}",
            entry_type="insight",
            metadata={"step": step},
            tags=["analysis", "conclusion"],
        )

        return {"summary": "Conclusions drawn", "conclusions": response}

    def _execute_save(self, step: str) -> Dict[str, Any]:
        """
        Save analysis results to memory.
        """
        # Get the last conclusion from context
        conclusion = self._get_last_conclusion()

        if conclusion:
            # Save to memory
            memory.remember(
                content=conclusion[:500] + "...",
                entry_type="insight",
                metadata={
                    "source": "Analyst Agent",
                    "task": self.context.goal if self.context else "Analysis",
                },
                tags=[
                    "analysis",
                    "insight",
                    self.context.goal.split()[0] if self.context else "general",
                ],
            )

            return {
                "summary": "Analysis saved to memory",
                "saved": True,
                "content": conclusion[:200] + "...",
            }
        else:
            return {"summary": "No conclusion to save", "saved": False}

    def _execute_general(self, step: str) -> Dict[str, Any]:
        """
        Handle general steps using the LLM.
        """
        # Get context from memory
        context = memory.recall(limit=5)

        system_prompt = """You are a helpful analysis assistant. Handle the given task."""

        user_prompt = f"Context:\n{context}\n\nTask: {step}\n\nProvide a detailed response."

        response = self.ask_llm(system_prompt, user_prompt)

        return {"summary": f"Completed: {step[:50]}...", "response": response}

    def _get_last_patterns(self) -> Optional[str]:
        """Get the last patterns from context."""
        if not self.context:
            return None

        for result in reversed(self.context.results):
            if isinstance(result, dict) and result.get("patterns"):
                return result["patterns"]
        return None

    def _get_last_comparison(self) -> Optional[str]:
        """Get the last comparison from context."""
        if not self.context:
            return None

        for result in reversed(self.context.results):
            if isinstance(result, dict) and result.get("comparison"):
                return result["comparison"]
        return None

    def _get_last_conclusion(self) -> Optional[str]:
        """Get the last conclusion from context."""
        if not self.context:
            return None

        for result in reversed(self.context.results):
            if isinstance(result, dict) and result.get("conclusions"):
                return result["conclusions"]
        return None

    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect on the result and decide next steps.
        """
        log.info("Analyst reflecting on step result...")

        # If error, continue but note it
        if result.get("error"):
            return {
                "should_stop": False,
                "reason": "Error occurred but continuing",
                "next_step": None,
            }

        # Check if we've completed enough steps
        if self.context and self.context.current_step >= 5:
            return {"should_stop": True, "reason": "Analysis completed"}

        return {"should_stop": False, "reason": "Continuing analysis", "next_step": None}
