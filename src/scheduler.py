# src/scheduler.py
# ============================================
# COMPETITORINTEL - Flexible Scheduler
#
# PURPOSE: Run reports automatically based on config
# ============================================

import time
from typing import Any, Dict

import schedule

from src.runner import TopicRunner
from src.utils.logger import log


class ReportScheduler:
    """
    Flexible scheduler that reads schedule from config.
    """

    def __init__(self, config_path: str = "topics.yaml"):
        self.config_path = config_path
        self.runner = TopicRunner(config_path)
        self.jobs = []
        log.info("ReportScheduler initialized")

    def setup_schedules(self) -> None:
        """
        Set up schedules based on topics in config.
        """
        for topic in self.runner.topics:
            name = topic.get("name", "Unnamed")
            schedule_config = topic.get("schedule", {})

            if not schedule_config:
                log.info(f"No schedule configured for '{name}', skipping")
                continue

            frequency = schedule_config.get("frequency", "weekly")

            if frequency == "daily":
                self._schedule_daily(name, schedule_config)
            elif frequency == "weekly":
                self._schedule_weekly(name, schedule_config)
            elif frequency == "monthly":
                self._schedule_monthly(name, schedule_config)
            elif frequency == "hourly":
                self._schedule_hourly(name, schedule_config)
            else:
                log.warning(f"Unknown frequency '{frequency}' for '{name}', skipping")

    def _schedule_daily(self, name: str, config: Dict[str, Any]) -> None:
        """Schedule a daily report."""
        time_str = config.get("time", "09:00")
        schedule.every().day.at(time_str).do(self._run_topic, name)
        log.info(f"Scheduled '{name}' daily at {time_str}")

    def _schedule_weekly(self, name: str, config: Dict[str, Any]) -> None:
        """Schedule a weekly report."""
        day = config.get("day", "monday").lower()
        time_str = config.get("time", "09:00")

        # Map day names to schedule methods
        day_map = {
            "monday": schedule.every().monday,
            "tuesday": schedule.every().tuesday,
            "wednesday": schedule.every().wednesday,
            "thursday": schedule.every().thursday,
            "friday": schedule.every().friday,
            "saturday": schedule.every().saturday,
            "sunday": schedule.every().sunday,
        }

        if day in day_map:
            day_map[day].at(time_str).do(self._run_topic, name)
            log.info(f"Scheduled '{name}' weekly on {day} at {time_str}")
        else:
            log.warning(f"Invalid day '{day}' for '{name}', defaulting to monday")
            schedule.every().monday.at(time_str).do(self._run_topic, name)

    def _schedule_monthly(self, name: str, config: Dict[str, Any]) -> None:
        """Schedule a monthly report."""
        day = config.get("day", 1)
        time_str = config.get("time", "09:00")

        if isinstance(day, int) and 1 <= day <= 28:
            # Use the schedule library's monthly scheduling
            schedule.every().month.at(day, time_str).do(self._run_topic, name)
            log.info(f"Scheduled '{name}' monthly on day {day} at {time_str}")
        else:
            log.warning(f"Invalid day '{day}' for '{name}', defaulting to 1st")
            schedule.every().month.at(1, time_str).do(self._run_topic, name)

    def _schedule_hourly(self, name: str, config: Dict[str, Any]) -> None:
        """Schedule an hourly report."""
        interval = config.get("interval", 1)
        schedule.every(interval).hours.do(self._run_topic, name)
        log.info(f"Scheduled '{name}' every {interval} hour(s)")

    def _run_topic(self, topic_name: str) -> None:
        """Run a specific topic."""
        log.info(f"Scheduled run for: {topic_name}")
        try:
            topic = None
            for t in self.runner.topics:
                if t.get("name") == topic_name:
                    topic = t
                    break

            if topic:
                result = self.runner.run_topic(topic)
                if result.get("status") == "success":
                    log.info(f"Scheduled run completed for '{topic_name}'")
                else:
                    log.error(f"Scheduled run failed for '{topic_name}'")
            else:
                log.error(f"Topic not found: {topic_name}")
        except Exception as e:
            log.error(f"Scheduled run failed: {e}")

    def run_forever(self) -> None:
        """Run the scheduler loop."""
        self.setup_schedules()

        # Log all scheduled jobs
        jobs = schedule.get_jobs()
        if jobs:
            log.info(f"Scheduler running with {len(jobs)} jobs")
            for job in jobs:
                log.info(f"  - {job}")
        else:
            log.warning("No jobs scheduled")

        log.info("Press Ctrl+C to stop")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            log.info("Scheduler stopped")


def run_scheduler(config_path: str = "topics.yaml") -> None:
    """Entry point for scheduler."""
    scheduler = ReportScheduler(config_path)
    scheduler.run_forever()


if __name__ == "__main__":
    run_scheduler()
