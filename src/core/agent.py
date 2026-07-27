import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from core.memory import memory
from llm.client import llm_client
from utils.logger import log
from utils.trace import publish_trace


class AgentContext:
    """
    store all the states for an agent's current task
    """

    def __init__(self, task_id: str, goal: str):
        self.task_id = task_id
        self.goal = goal
        self.status = "pending"
        self.steps_taken: List[str] = [] # what the agent di
        self.observation: List[str] = [] # what the agent saw
        self.results: List[Dict[str, Any]] = [] # what the agent produced
        self.errors: List[str] = [] # what went wrong
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.current_step = 0

    def add_step(self, step_description: str) -> None:
        self.steps_taken.append(step_description)
        log.info(f"[{self.task_id}] Step: {step_description}")

    def add_observation(self, observation: str) -> None:
        self.observation.append(observation)
        log.debug(f"[{self.task_id}] Observation: {observation}")

    def add_result(self, result: Dict[str, Any]) -> None:
        self.results.append(result)
        log.debug(f"[{self.task_id}] Result: {result.get('summary', 'No summary')}")

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        log.error(f"[self.task_id] Error: {error}")


class BaseAgent(ABC):
    """
    Abstract base class for all agents,
    subclasses must implement plan() (breaking the goal into steps) , execute_step() (does one step) and reflect() (thinks about what happened)
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.context: Optional[AgentContext] = None
        self.llm = llm_client
        log.info(f"Agent '{name}' initialized")

    @abstractmethod
    def plan(self, goal: str):
        """Break down the goal into specific steps"""
        pass

    @abstractmethod
    def execute_step(self, step: str):
        """Execute a single step"""
        pass

    @abstractmethod
    def reflect(self, result: Dict[str, Any]):
        """reflect on the result of a step"""
        pass

    # THE MAIN RUN METHOD SHARED BY ALL AGENTS
    def run(self, goal: str, max_steps: int = 10) -> Dict[str, Any]:
        """
        The ReAct loop: plan -> execute -> reflect -> repeat
        :param goal:
        :param max_steps:
        :return:
        """

        #-- 1. Initialize
        task_id = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.context = AgentContext(task_id, goal)
        self.context.status = "running"
        self.context.started_at = datetime.now()

        log.info(f"Agent '{self.name}' starting task: '{goal}'")

        try:
            #2. Plan
            self.context.add_step("Planning....")
            steps = self.plan(goal)
            self.context.add_step(f"Planned {len(steps)} steps")
            log.info(f"Agent '{self.name}' planned {len(steps)} steps")

            #3. Execute each step
            for step_index, step in enumerate(steps, 1):
                if step_index > max_steps:
                    log.info(f"Stopping after {max_steps} (limit reached)")
                    break

                publish_trace(self.name, f"Step {step_index}: {step[:100]}")

                self.context.current_step = step_index
                self.context.add_step(f"Executing step {step_index}: {step}")

                try:

                    #ACT
                    result = self.execute_step(step)

                    if result:
                        summary = result.get("summary", f"Step {step_index} completed")
                        memory.remember(
                            content=f"{self.name}: {summary}",
                            entry_type="step_result",
                            metadata={"step": step, "step_index": step_index},
                            tags=[self.name.lower(), "step"],
                        )

                    #OBSERVE
                    self.context.add_result(result)
                    self.context.add_observation(result.get("summary", "Step Completed"))

                    #REFLECT
                    reflection = self.reflect(result)

                    #CHECK IF WE SHOULD STOP
                    if reflection.get("should_stop", False):
                        reason = reflection.get("reason", "Agent decided to stop")
                        self.context.add_step(f"Stopping early: {reason}")
                        break

                    #add new step if suggested
                    next_step = reflection.get("next_step")
                    if next_step and step_index < max_steps:
                        steps.insert(step_index + 1, next_step)
                        self.context.add_step(f"Added new step: {next_step}")

                except Exception as e:
                    error_msg = f"Step {step_index} failed: {str(e)}"
                    self.context.add_error(error_msg)
                    self.context.add_step(f"ERROR: {error_msg}")
                    log.error(f"[{task_id}] {error_msg}")
                    continue
            #4. Finalize
            self.context.status = "completed"
            self.context.completed_at = datetime.now()

            self._auto_save_report()

            return {
                "status": "success",
                "result": self._synthesize_results(),
                "context": self.context,
            }

        except Exception as e:
            # error_msg = f'Step {step_index} failed'
            self.context.completed_at =  datetime.now()
            self.context.add_error(str(e))
            log.error(f"Agent {self.name}' failed: {e}")

            return {
                "status": "failed",
                "error": str(e),
                "context": self.context
            }

    def _synthesize_results(self) -> Dict[str, Any]:
        """
        Combine all step results into an output
        :return:
        """
        if not self.context or self.context.results:
            return {
                "Message": "No results provided"
            }

        all_results = self.context.results
        summaries = [r.get("summary", "") for r in all_results if r.get("summary")]

        return {
            "total_steps":len(self.context.steps_taken),
            "results" : all_results,
            "summary": " | ".join(summaries) if summaries else "Completed all steps",
            "observations" : self.context.observation,
            "errors": self.context.errors
        }

    def ask_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Helper methods for subclasses to talk to the LLM"""
        return self.llm.chat_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

    def _auto_save_report(self) -> None:
        """
        Automatically save any report found in the agent's results.
        This ensures reports are saved even if the agent stops early.
        """
        import os
        from datetime import datetime

        if not self.context:
            return

        # Look for a report in the results
        report = None
        filename = None

        for result in self.context.results:
            if isinstance(result, dict):
                # Check for report in various forms
                if result.get("report"):
                    report = result["report"]
                    break
                elif result.get("polished_report"):
                    report = result["polished_report"]
                    break
                elif result.get("content") and "report" in result.get("summary", "").lower():
                    # Some agents store the report as content
                    report = result["content"]
                    break

        # Also check if any result already has a filename (already saved)
        for result in self.context.results:
            if isinstance(result, dict) and result.get("filename"):
                log.info(f"Report already saved: {result.get('filename')}")
                return

        # If we found a report, save it
        if report:
            try:
                os.makedirs("reports", exist_ok=True)

                # Generate filename from agent name and topic
                topic = self.context.goal[:30].replace(" ", "_").replace("/", "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"report_{self.name}_{topic}_{timestamp}.md"
                filepath = f"reports/{filename}"

                with open(filepath, "w") as f:
                    f.write(report)

                log.info(f"✅ Auto-saved report to {filepath}")

                # Add the filename to results so it can be accessed later
                self.context.add_result(
                    {
                        "summary": f"Report auto-saved: {filename}",
                        "filename": filename,
                        "filepath": filepath,
                        "report": report,
                    }
                )

            except Exception as e:
                log.error(f"Failed to auto-save report: {e}")
        else:
            # Check if there are any memories that might contain a report
            # Some agents save reports to memory directly
            pass

    def _publish_trace(self, agent: str, action: str, content: str = ""):
        """Publish a trace to the SSE stream."""
        try:
            # Get the current run_id from environment or context
            run_id = os.environ.get("CURRENT_RUN_ID")
            if run_id:
                # Send to the SSE endpoint
                requests.post(
                    "http://localhost:5000/api/publish_trace",
                    json={"run_id": run_id, "agent": agent, "action": action, "content": content},
                    timeout=1,
                )
        except Exception:
            pass  # Silently fail so it doesn't break the agent
