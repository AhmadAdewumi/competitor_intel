# src/agents/researcher.py
import re

# Researcher Agent#
# Research topics by searching and scraping web pages.
# Uses Search Tool + Scrape Tool to research.
from typing import Any, Dict, List, Optional

from src.core.agent import BaseAgent
from src.core.memory import memory
from src.tools.calculator import CalculatorTool
from src.tools.scrape import ScrapeTool
from src.tools.search import SearchTool
from src.utils.logger import log
from src.utils.trace import publish_trace


class ResearcherAgent(BaseAgent):
    """
    An agent that researches topics by searching and scraping.

    How it works:
    1. Search for information on the web
    2. Scrape the top results
    3. Summarize the findings
    4. Return a research report

    Uses:
    - SearchTool: Finds relevant web pages
    - ScrapeTool: Extracts content from pages
    - CalculatorTool: For any calculations needed
    """

    def __init__(self):
        super().__init__(
            name="Researcher",
            description="Researches topics by searching the web, scraping pages, and summarizing findings.",
        )

        # Initialize tools
        self.search_tool = SearchTool()
        self.scrape_tool = ScrapeTool()
        self.calculator_tool = CalculatorTool()

        log.info("Researcher Agent initialized with tools")

    def plan(self, goal: str) -> List[str]:
        """
        Break down the research goal into steps.

        Args:
            goal: What to research

        Returns:
            List of steps to execute
        """

        log.info(f"Researcher planning for: {goal}")

        # Using the LLM to plan the research
        system_prompt = """You are a research planner. Break down the research goal into specific steps.

        For a research task, typical steps are:
        1. Search for information on the topic
        2. Scrape the top results to get detailed content
        3. Analyze and summarize the findings
        4. Write a research report

        Return a list of steps (one per line).
        Be specific about what to search for."""

        user_prompt = f"Research goal: {goal}\n\nBreak this down into specific steps."

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
                f"Search for information about: {goal}",
                "Scrape the top search results for detailed content",
                "Summarize the findings",
                "Write a research report",
            ]

        log.info(f"Planned {len(steps)} steps")
        return steps

    def execute_step(self, step: str) -> Dict[str, Any]:
        """
        Execute a single step in the research plan.

        Args:
            step: The step to execute

        Returns:
            Dict with the result
        """

        log.info(f"Executing step: {step}")
        step_lower = step.lower()

        # Step 1: Search
        if "search" in step_lower or "find" in step_lower:
            return self._execute_search(step)

        # Step 2: Scrape
        elif "scrape" in step_lower or "read" in step_lower or "extract" in step_lower:
            return self._execute_scrape(step)

        # Step 3: Summarize
        elif "summarize" in step_lower or "analyze" in step_lower or "synthesize" in step_lower:
            return self._execute_summarize(step)

        # Step 4: Write report
        elif "report" in step_lower or "write" in step_lower:
            return self._execute_report(step)

        # Default: Using LLM to handle it
        else:
            return self._execute_general(step)

    def _execute_search(self, step: str) -> Dict[str, Any]:
        """
        Execute a search step.
        """

        query_match = re.search(r'"([^"]*)"', step)

        if query_match:
            query = query_match.group(1)
        else:
            query = step.replace("Search", "").replace("for", "").replace("about", "").strip()

        log.info(f"Searching for: {query}")
        publish_trace("Researcher", f'Searching: "{query}"')

        # Use the search tool
        result = self.search_tool.run({"query": query, "max_results": 2})

        if result["success"]:
            for item in result["results"][:2]:
                memory.remember(
                    content=f"Found: {item.get('title', 'No title')} - {item.get('url', 'No URL')}",
                    entry_type="research",
                    metadata={"url": item.get("url"), "snippet": item.get("snippet", "")},
                    tags=["search", "web"],
                )

            publish_trace("Researcher", f'Found {result["count"]} results for "{query}"')

            return {
                "summary": f"Found {result['count']} results for '{query}'",
                "results": result["results"],
                "query": query,
            }
        else:
            publish_trace("Researcher", f"Search failed: {result.get('error')}")
            return {
                "summary": f"Search failed: {result.get('error', 'Unknown error')}",
                "error": result.get("error"),
            }

    def _execute_scrape(self, step: str) -> Dict[str, Any]:
        """
        Execute a scrape step.

        Uses the results from the search step to scrape pages.
        """
        # Check if we have search results in context
        search_results = self._get_search_results()

        if not search_results:
            return {
                "summary": "No search results available to scrape. Please run a search first.",
                "error": "No search results",
            }

        # Scrape the top results
        scraped_pages = []
        for result in search_results[:2]:
            url = result.get("url")
            if url:
                log.info(f"Scraping: {url}")
                scrape_result = self.scrape_tool.run({"url": url, "max_chars": 1500})

                if scrape_result["success"]:
                    memory.remember(
                        content=f"Scraped: {scrape_result.get('title', 'No title')} - {scrape_result.get('content', '')[:200]}...",
                        entry_type="fact",
                        metadata={"url": url, "title": scrape_result.get("title")},
                        tags=["scrape", "web"],
                    )

                    scraped_pages.append(
                        {
                            "url": url,
                            "title": scrape_result.get("title", ""),
                            "content": scrape_result.get("content", ""),
                            "headings": scrape_result.get("headings", []),
                        }
                    )
                else:
                    log.warning(f"Failed to scrape {url}: {scrape_result.get('error')}")

        return {
            "summary": f"Scraped {len(scraped_pages)} pages",
            "pages": scraped_pages,
            "count": len(scraped_pages),
        }

    def _execute_summarize(self, step: str) -> Dict[str, Any]:
        """
        Summarize the scraped content.

        Uses the LLM to summarize the collected information.
        """
        # Get scraped content from context
        scraped_pages = self._get_scraped_pages()

        if not scraped_pages:
            return {
                "summary": "No scraped content to summarize. Please scrape some pages first.",
                "error": "No content",
            }

        # Combine all content
        combined_content = ""
        for page in scraped_pages:
            combined_content += f"\n--- {page['title']} ---\n{page['content'][:1000]}\n"

        # Use LLM to summarize
        system_prompt = """You are a research analyst. Summarize the provided content clearly and concisely.

        Organize the summary by:
        1. Key findings
        2. Important details
        3. Notable quotes or data
        4. Overall conclusions

        Keep the summary focused and informative."""

        user_prompt = (
            f"Here is the content to summarize:\n\n{combined_content}\n\nProvide a clear summary."
        )

        response = self.ask_llm(system_prompt, user_prompt)

        return {
            "summary": "Research summary generated",
            "content": response,
            "pages_analyzed": len(scraped_pages),
        }

    def _execute_report(self, step: str) -> Dict[str, Any]:
        """
        Write a final research report.

        Combines all research into a polished report.
        """
        # Get the summary from context
        summary = self._get_last_summary()

        if not summary:
            return {
                "summary": "No summary available to write a report. Please summarize first.",
                "error": "No summary",
            }

        # Get the goal from context
        goal = self.context.goal if self.context else "Research topic"

        # Use LLM to write the report
        system_prompt = """You are a professional research writer. Create a well-structured research report.

        The report should include:
        1. Executive Summary
        2. Key Findings
        3. Detailed Analysis
        4. Conclusions
        5. Recommendations

        Write in a professional, clear style."""

        user_prompt = f"""Research Goal: {goal}

        Research Summary:
        {summary}

        Write a comprehensive research report based on this information."""

        response = self.ask_llm(system_prompt, user_prompt)

        return {"summary": "Research report written", "report": response, "topic": goal}

    def _execute_general(self, step: str) -> Dict[str, Any]:
        """
        Handle general steps using the LLM.
        """
        system_prompt = "You are a helpful research assistant. Handle the given task."
        user_prompt = f"Task: {step}\n\nProvide a detailed response."

        response = self.ask_llm(system_prompt, user_prompt)

        return {"summary": f"Completed: {step[:50]}...", "response": response}

    def _get_search_results(self) -> List[Dict[str, Any]]:
        """Get search results from the agent's context."""
        if not self.context:
            return []

        for result in self.context.results:
            if "results" in result and isinstance(result["results"], list):
                return result["results"]

        return []

    def _get_scraped_pages(self) -> List[Dict[str, Any]]:
        """Get scraped pages from the agent's context."""
        if not self.context:
            return []

        for result in self.context.results:
            if "pages" in result and isinstance(result["pages"], list):
                return result["pages"]

        return []

    def _get_last_summary(self) -> Optional[str]:
        """Get the last summary from the agent's context."""
        if not self.context:
            return None

        for result in reversed(self.context.results):
            if "content" in result and "summary" in result.get("summary", ""):
                return result["content"]

        return None

    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reflect on the result of a step.

        Decides whether to continue or stop.
        """
        log.info("Reflecting on step result...")

        # If there was an error, we can continue but note it
        if result.get("error"):
            return {
                "should_stop": False,
                "reason": "Error occurred but continuing",
                "next_step": None,
            }

        # Check if we've completed all steps
        if self.context and self.context.current_step >= 4:
            return {"should_stop": True, "reason": "Research completed"}

        # Check if the result suggests next steps
        if "next_step" in result:
            return {
                "should_stop": False,
                "reason": "Agent suggests next step",
                "next_step": result["next_step"],
            }

        # Default: Continue
        return {"should_stop": False, "reason": "Continuing research", "next_step": None}
