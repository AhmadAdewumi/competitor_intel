# src/runner.py
# Full updated version

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from src.agents.orchestrator import Orchestrator
from src.config.constants import AgentLimits
from src.utils.email_sender import send_report_email
from src.utils.logger import log
from src.utils.report_formatter import (
    generate_html_report,
    is_report_meaningful,
    save_html,
    save_pdf,
)


class TopicRunner:
    """
    Runs research on topics defined in a config file.
    """

    def __init__(self, config_path: str = "topics.yaml"):
        self.config_path = config_path
        self.topics = []
        self.orchestrator = Orchestrator()

        if os.path.exists(config_path):
            self.load_config()
        else:
            log.warning(f"Config file '{config_path}' not found")

    def load_config(self) -> None:
        """Load topics from src.config file."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                self.topics = config.get("topics", [])
                log.info(f"Loaded {len(self.topics)} topics from config")
        except Exception as e:
            log.error(f"Failed to load config: {e}")
            self.topics = []

    def get_topic_names(self) -> List[str]:
        """Get list of all topic names."""
        return [t.get("name", "Unnamed") for t in self.topics]

    def run_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run research on a single topic.
        """
        # Generate run_id and set environment variable
        run_id = os.environ.get("CURRENT_RUN_ID")
        if not run_id:
            run_id = f"run_{topic.get('id', 0)}_{int(datetime.now().timestamp())}"
            os.environ["CURRENT_RUN_ID"] = run_id

        name = topic.get("name", "Unnamed")

        description = topic.get("description", name)
        search_terms = topic.get("search_terms", [])
        urls = topic.get("urls", [])

        # ============================================
        # PUBLISH TRACE: Start
        # ============================================
        from src.utils.trace import publish_trace

        publish_trace("Orchestrator", f"Starting research on: {name}")

        log.info(f"\n{'=' * 60}")
        log.info(f"📚 Starting research on: {name}")
        log.info(f"{'=' * 60}")

        # Build the goal
        goal = f"Research {name}"
        if description:
            goal += f": {description}"
        if search_terms:
            goal += f". Search specifically for: {', '.join(search_terms)}"
        if urls:
            goal += f". Also analyze these specific websites: {', '.join(urls)}"

        # ============================================
        # PUBLISH TRACE: Planning
        # ============================================
        publish_trace("Orchestrator", f"Planning research for: {name}")

        # Run the orchestrator
        result = self.orchestrator.run(goal, max_steps=AgentLimits.RUNNER_MAX_STEPS)

        # Process result
        if result.get("status") == "success":
            log.info(f"✅ Orchestrator completed for '{name}'")
            publish_trace("Orchestrator", f"Research completed for: {name}")

            # Try to extract report
            report = self._extract_report(result)

            # If no report found, check if any report file was created recently
            if not report:
                import glob

                report_files = glob.glob("reports/*.md")
                if report_files:
                    # Sort by modification time
                    latest = max(report_files, key=os.path.getmtime)
                    if (
                        os.path.getmtime(latest) > datetime.now().timestamp() - 60
                    ):  # Last 60 seconds
                        with open(latest, "r") as f:
                            report = f.read()
                        log.info(f"📄 Found report file: {latest}")
                        publish_trace("Orchestrator", f"Found report file: {latest}")

            if report and is_report_meaningful(report):
                log.info(f"📄 Meaningful report generated ({len(report)} characters)")
                publish_trace("Orchestrator", f"Report generated ({len(report)} characters)")
                self._save_and_send_report(result, topic, report)
                result["report_generated"] = True
            else:
                log.warning(f"⚠️ No meaningful report found for '{name}'")
                publish_trace("Orchestrator", f"No meaningful report found for: {name}")
                # Log what was in the results to help debug
                if result.get("context"):
                    log.debug(f"Context results: {len(result['context'].results)} items")
                    for i, r in enumerate(result["context"].results):
                        if isinstance(r, dict):
                            log.debug(f"  Result {i}: keys = {list(r.keys())}")
                result["report_generated"] = False
        else:
            log.error(f"❌ Orchestrator failed for '{name}': {result.get('error')}")
            publish_trace("Orchestrator", f"Research failed: {result.get('error')}")

        # Clear the run_id
        os.environ.pop("CURRENT_RUN_ID", None)

        return result

    def _extract_report(self, result: Dict[str, Any]) -> Optional[str]:
        """
        Extract report from result using multiple strategies.
        """
        # Strategy 1: Direct result
        final_result = result.get("result", {})
        if isinstance(final_result, dict):
            for key in ["report", "polished_report", "content"]:
                content = final_result.get(key)
                if content and isinstance(content, str) and len(content) > 200:
                    log.debug(f"Found report in result['{key}']")
                    return content

        # Strategy 2: Check context results (most likely place)
        context = result.get("context")
        if context and hasattr(context, "results"):
            log.debug(f"Checking {len(context.results)} context results")
            for i, r in enumerate(context.results):
                if isinstance(r, dict):
                    if r.get("report"):
                        log.debug(f"Found report in context result {i}")
                        return r["report"]
                    elif r.get("polished_report"):
                        log.debug(f"Found polished_report in context result {i}")
                        return r["polished_report"]
                    elif r.get("content"):
                        content = r["content"]
                        if (
                            isinstance(content, str)
                            and len(content) > 500
                            and ("#" in content or "**" in content)
                        ):
                            log.debug(f"Found content in context result {i}")
                            return content

        # Strategy 3: Check if the Writer agent already saved it
        import glob  # Only import glob here, NOT os

        goal = result.get("context", {}).goal if hasattr(result.get("context", {}), "goal") else ""
        if goal:
            report_files = glob.glob("reports/*.md")
            if report_files:
                latest = max(report_files, key=os.path.getmtime)  # os is already imported at top
                if os.path.getmtime(latest) > datetime.now().timestamp() - 120:
                    log.debug(f"Found recent report file: {latest}")
                    with open(latest, "r") as f:
                        content = f.read()
                        if len(content) > 200:
                            return content

        return None

    def run_all(self) -> List[Dict[str, Any]]:
        """Run research on ALL topics."""
        results = []
        total = len(self.topics)

        for i, topic in enumerate(self.topics, 1):
            log.info(f"\n{'#' * 60}")
            log.info(f"📊 Topic {i}/{total}")
            log.info(f"{'#' * 60}")

            result = self.run_topic(topic)
            results.append({"topic": topic.get("name", "Unnamed"), "result": result})

        return results

    def _save_and_send_report(
        self, result: Dict[str, Any], topic: Dict[str, Any], report_content: str
    ) -> None:
        """
        Save report and send via email.
        """
        name = topic.get("name", "Unnamed")

        # Create directories
        os.makedirs("reports", exist_ok=True)
        os.makedirs("reports/html", exist_ok=True)
        os.makedirs("reports/pdf", exist_ok=True)

        # Generate filenames
        safe_name = name.lower().replace(" ", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        md_path = f"reports/{safe_name}_{timestamp}.md"
        html_path = f"reports/html/{safe_name}_{timestamp}.html"
        pdf_path = f"reports/pdf/{safe_name}_{timestamp}.pdf"

        # 1. Save Markdown
        header = f"""# Research Report: {name}
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Topic:** {name}

---

"""
        with open(md_path, "w") as f:
            f.write(header + report_content)
        log.info(f"✅ Markdown saved to {md_path}")

        # 2. Generate and save HTML
        html_content = generate_html_report(report_content, name)
        if save_html(html_content, html_path):
            log.info(f"✅ HTML saved to {html_path}")

        # 3. Generate and save PDF
        if save_pdf(html_content, pdf_path):
            log.info(f"✅ PDF saved to {pdf_path}")

        # 4. Send email if configured
        email = topic.get("email")
        if email:
            log.info(f"📧 Sending report to {email}...")
            success = send_report_email(
                to_email=email,
                topic_name=name,
                report_content=report_content,
                report_paths=[md_path, pdf_path],
                html_content=html_content,
            )
            if success:
                log.info(f"✅ Email sent to {email}")
            else:
                log.warning(f"⚠️ Failed to send email to {email}")

    def get_latest_report(self, topic_name: str) -> Optional[str]:
        """Get the latest report for a topic."""
        safe_name = topic_name.lower().replace(" ", "_").replace("/", "_")
        reports = [f for f in os.listdir("reports") if f.startswith(safe_name)]
        if reports:
            reports.sort(reverse=True)
            return f"reports/{reports[0]}"
        return None


def run_single_topic(topic_name: str) -> None:
    """Run research on a single topic provided via CLI."""
    log.info(f"🚀 Running single topic: '{topic_name}'")

    orchestrator = Orchestrator()
    goal = f"Research {topic_name} comprehensively"

    result = orchestrator.run(goal, max_steps=AgentLimits.RUNNER_MAX_STEPS)

    if result.get("status") == "success":
        log.info(f"✅ Research completed for '{topic_name}'")

        # Try to extract report
        final_result = result.get("result", {})
        report = None

        if isinstance(final_result, dict):
            report = final_result.get("report") or final_result.get("polished_report")

        if report and is_report_meaningful(report):
            # Save the report
            os.makedirs("reports", exist_ok=True)
            safe_name = topic_name.lower().replace(" ", "_").replace("/", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"reports/{safe_name}_{timestamp}.md"

            header = f"# Research Report: {topic_name}\n\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            with open(filepath, "w") as f:
                f.write(header + report)
            log.info(f"✅ Report saved to {filepath}")
        else:
            log.warning("⚠️ No meaningful report generated")
    else:
        log.error(f"❌ Failed to research '{topic_name}': {result.get('error')}")
