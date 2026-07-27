# src/agents/orchestrator.py
# ============================================
# COMPETITORINTEL - Orchestrator Agent
# ============================================
#
# PURPOSE: Coordinate all agents to complete complex tasks.
# WHY: Multiple agents working together are more powerful.
# WHAT: Delegates tasks to Researcher, Analyst, and Writer.
# ============================================

from typing import Any, Dict, List

from src.agents.analyst import AnalystAgent
from src.agents.researcher import ResearcherAgent
from src.agents.writer import WriterAgent
from src.config.constants import AgentLimits
from src.core.agent import BaseAgent
from src.core.memory import memory
from src.utils.logger import log


class Orchestrator(BaseAgent):
    """
    An agent that coordinates all other agents to complete complex tasks.

    How it works:
    1. Receives a complex goal
    2. Breaks it down into sub-tasks
    3. Delegates to the right agents
    4. Monitors progress
    5. Combines results
    """

    def __init__(self):
        super().__init__(
            name="Orchestrator",
            description="Coordinates Researcher, Analyst, and Writer agents to complete complex tasks.",
        )

        # Initialize all agents
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()

        log.info("Orchestrator initialized with all agents")

    def plan(self, goal: str) -> List[str]:
        """
        Break down the complex goal into a workflow.
        """
        log.info(f"Orchestrator planning for: {goal}")

        # Using the LLM to plan the workflow
        system_prompt = """You are a project orchestrator. Break down the goal into a workflow of tasks.

           IMPORTANT: You MUST use ALL three agents in order:
           1. FIRST: Researcher - Searches the web and gathers information
           2. SECOND: Analyst - Analyzes the gathered data
           3. THIRD: Writer - Writes a complete professional report

           Keep it to 3-5 steps maximum.
           Do not create more than 5 steps.

           Return a list of tasks (one per line). Use ALL three agents."""

        user_prompt = f"Goal: {goal}\n\nBreak this down into a MAXIMUM of 5 steps."

        response = self.ask_llm(system_prompt, user_prompt)

        # Parse the response into steps
        steps = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                clean_line = line
                if line[0].isdigit() and ". " in line:
                    clean_line = line.split(". ", 1)[1] if ". " in line else line
                elif line.startswith("- "):
                    clean_line = line[2:]
                elif line.startswith("* "):
                    clean_line = line[2:]

                if clean_line:
                    steps.append(clean_line)

        # HARD LIMIT: Only keep the first 3-5 steps
        if len(steps) > 15:
            log.warning(f"Planned {len(steps)} steps, truncating to 5")
            steps = steps[:5]

        # If no steps were parsed, use default workflow
        if not steps:
            steps = [
                "Researcher: Research the topic and gather information",
                "Analyst: Analyze the research findings",
                "Writer: Write a comprehensive report",
            ]

        log.info(f"Planned {len(steps)} steps")
        return steps

    def execute_step(self, step: str) -> Dict[str, Any]:
        """
        Execute a single step in the workflow.
        """
        log.info(f"Executing step: {step}")
        step_lower = step.lower()

        # Determine which agent to use
        if "researcher" in step_lower:
            return self._execute_researcher(step)
        elif "writer" in step_lower:
            return self._execute_writer(step)
        elif "analyst" in step_lower:
            return self._execute_analyst(step)
        else:
            # Default: Try to infer the agent
            return self._execute_inferred(step)

    def _execute_researcher(self, step: str) -> Dict[str, Any]:
        """
        Execute a researcher task.
        """
        # Extract the research topic
        topic = self._extract_topic(step)

        log.info(f"Starting researcher on: {topic}")

        # Use memory to store the topic
        memory.remember(
            content=f"Research task: {topic}", entry_type="task", metadata={"agent": "researcher"}
        )

        # Run the researcher
        result = self.researcher.run(topic, max_steps=AgentLimits.RESEARCHER_MAX_STEPS)

        if result["status"] == "success":
            # Save the result to memory
            memory.remember(
                content=f"Researcher completed: {topic}",
                entry_type="research_complete",
                metadata={"result": result.get("result", {})},
            )

            return {"summary": f"Research completed on: {topic}", "result": result}
        else:
            return {
                "summary": f"Research failed on: {topic}",
                "error": result.get("error", "Unknown error"),
            }

    def _execute_analyst(self, step: str) -> Dict[str, Any]:
        """
        Execute an analyst task.
        """
        # Extract the analysis topic
        topic = self._extract_topic(step)

        log.info(f"Starting analyst on: {topic}")

        # Run the analyst
        result = self.analyst.run(topic, max_steps=AgentLimits.ANALYST_MAX_STEPS)

        if result["status"] == "success":
            # Save the result to memory
            memory.remember(
                content=f"Analyst completed: {topic}",
                entry_type="analysis_complete",
                metadata={"result": result.get("result", {})},
            )

            return {"summary": f"Analysis completed on: {topic}", "result": result}
        else:
            return {
                "summary": f"Analysis failed on: {topic}",
                "error": result.get("error", "Unknown error"),
            }

    def _execute_writer(self, step: str) -> Dict[str, Any]:
        """
        Execute a writer task.
        """

        topic = step.replace("Writer:", "").replace("Writer", "").strip()

        # If the topic references the analyst, use a better default
        if "analyst" in topic.lower() or len(topic) < 10:
            topic = "AI customer service tools competitive analysis"

        log.info(f"Starting writer on: {topic}")

        # Run the writer with MORE steps
        result = self.writer.run(topic, max_steps=AgentLimits.WRITER_MAX_STEPS)

        if result["status"] == "success":
            # Save the result to memory
            memory.remember(
                content=f"Writer completed: {topic}",
                entry_type="writing_complete",
                metadata={"result": result.get("result", {})},
            )

            # Check if a report was generated
            final_result = result.get("result", {})
            if isinstance(final_result, dict):
                report = final_result.get("report") or final_result.get("polished_report")
                if report:
                    # Save report to file
                    filename = self._save_report(report, topic)
                    return {
                        "summary": f"Report written: {filename}",
                        "report": report,
                        "filename": filename,
                        "result": result,
                    }

            return {"summary": f"Writing completed on: {topic}", "result": result}
        else:
            return {
                "summary": f"Writing failed on: {topic}",
                "error": result.get("error", "Unknown error"),
            }

    def _execute_inferred(self, step: str) -> Dict[str, Any]:
        """
        Execute a step by inferring which agent to use.
        """
        # Try to infer the agent from keywords
        step_lower = step.lower()

        if "search" in step_lower or "research" in step_lower or "find" in step_lower:
            return self._execute_researcher(step)
        elif "analyze" in step_lower or "pattern" in step_lower or "trend" in step_lower:
            return self._execute_analyst(step)
        elif "write" in step_lower or "report" in step_lower or "document" in step_lower:
            return self._execute_writer(step)
        else:
            # Default: Use the LLM
            response = self.ask_llm(
                system_prompt="You are a helpful assistant. Handle the given task.",
                user_prompt=f"Task: {step}\n\nProvide a detailed response.",
            )

            return {"summary": f"Completed: {step[:50]}...", "response": response}

    def _extract_topic(self, step: str) -> str:
        """
        Extract the topic from a step description.
        """
        # Try to find the topic after common patterns
        import re

        # Look for "on" patterns
        match = re.search(r"on\s+([^.]+)", step, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Look for "about" patterns
        match = re.search(r"about\s+([^.]+)", step, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Look for quotes
        match = re.search(r'"([^"]*)"', step)
        if match:
            return match.group(1)

        # Use the whole step as the topic
        return step

    def _save_report(self, report: str, topic: str) -> str:
        """
        Save a report to a file.
        """
        import os
        from datetime import datetime

        # Create reports directory
        os.makedirs("reports", exist_ok=True)

        # Generate filename from topic
        topic_clean = topic[:30].replace(" ", "_").replace("/", "_")
        filename = f"report_{topic_clean}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = f"reports/{filename}"

        with open(filepath, "w") as f:
            f.write(report)

        log.info(f"Report saved to {filepath}")
        return filename

    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect on the result and decide whether to stop.

        The Orchestrator should only stop when:
        1. The Writer agent has been called AND
        2. The Writer has completed its work (saved a report)
        """
        log.info(
            f"Orchestrator reflecting on step {self.context.current_step if self.context else '?'}..."
        )

        if result.get("error"):
            log.warning(f"Error in step, continuing: {result.get('error')}")
            return {"should_stop": False, "reason": "Error occurred but continuing"}

        if not self.context:
            return {"should_stop": False, "reason": "No context"}

        # Check if Writer has been called
        writer_called = False
        for step in self.context.steps_taken:
            if "writer" in step.lower() or "report" in step.lower():
                writer_called = True
                break

        # If Writer hasn't been called, we MUST continue
        if not writer_called:
            log.info("Writer not called yet, continuing")
            return {"should_stop": False, "reason": "Writer agent still needs to run"}

        # Check if Writer has actually saved a report
        writer_saved = False
        for step in self.context.steps_taken:
            if "save" in step.lower() or "report saved" in step.lower():
                writer_saved = True
                break

        # Check if we have a report in the results
        report_found = False
        for r in self.context.results:
            if isinstance(r, dict):
                if r.get("report") or r.get("polished_report") or r.get("filename"):
                    report_found = True
                    break

        # If Writer called AND (report saved OR report found), we're done
        if writer_called and (writer_saved or report_found):
            log.info("✅ Report generated and saved, workflow complete")
            return {"should_stop": True, "reason": "Workflow completed"}

        # If Writer called but no report yet, continue
        if writer_called and not (writer_saved or report_found):
            log.info("Writer called but report not ready, continuing")
            return {"should_stop": False, "reason": "Waiting for report"}

        # Default: continue
        return {"should_stop": False, "reason": "Continuing workflow"}

    # def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
    #     """Reflect on the result and decide next steps."""
    #     log.info("Orchestrator reflecting on step result...")
    #
    #     if result.get("error"):
    #         return {"should_stop": False, "reason": "Error occurred but continuing"}
    #
    #     # forcing Writer to be included
    #     # Check if Writer has been called yet
    #     writer_called = False
    #     if self.context:
    #         for step in self.context.steps_taken:
    #             if "writer" in step.lower() or "report" in step.lower():
    #                 writer_called = True
    #                 break
    #
    #     # If Writer hasn't been called, don't stop
    #     if not writer_called:
    #         return {"should_stop": False, "reason": "Writer agent still needs to run"}
    #
    #     # Check if we've completed enough steps
    #     if self.context and self.context.current_step >= 4:  # Increased from 3 to 4
    #         return {"should_stop": True, "reason": "Workflow completed"}
    #
    #     return {"should_stop": False, "reason": "Continuing workflow"}
