#!/usr/bin/env python
# main.py - CLI Entry Point for CompetitorIntel

import argparse
import sys
import os
from src.runner import TopicRunner, run_single_topic
from src.utils.logger import log


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CompetitorIntel - AI-powered competitive intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a single topic (quick research)
  python main.py --topic "AI customer service tools"

  # Run a specific topic from config file
  python main.py --topic-name "AI Customer Service Tools"

  # Run all topics from config
  python main.py --config topics.yaml

  # List all topics in config
  python main.py --list-topics
        """,
    )

    parser.add_argument("--topic", "-t", type=str, help="Single topic to research (quick mode)")

    parser.add_argument(
        "--topic-name", "-tn", type=str, help="Run a specific topic from the config file by name"
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="topics.yaml",
        help="Config file with topics (default: topics.yaml)",
    )

    parser.add_argument(
        "--list-topics", "-l", action="store_true", help="List all topics in the config file"
    )

    parser.add_argument(
        "--limit", "-n", type=int, default=None, help="Limit the number of topics to run"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    parser.add_argument(
        "--schedule", action="store_true", help="Run the scheduler (auto-run reports)"
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="topics.yaml",
        help="Config file path (default: topics.yaml)",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Set log level
    if args.verbose:
        os.environ["LOG_LEVEL"] = "DEBUG"

    # Single topic mode (quick)
    if args.topic:
        log.info(f"🚀 Running quick research on: '{args.topic}'")
        run_single_topic(args.topic)
        return

    # Config file mode
    if args.config:
        # Check if config file exists
        if not os.path.exists(args.config):
            log.error(f"Config file not found: {args.config}")
            log.info("Creating sample config file...")
            create_sample_config()
            log.info(f"Sample config created at: {args.config}")
            log.info("Edit it and run again.")
            return

        # Load topics
        runner = TopicRunner(args.config)

        # List topics mode
        if args.list_topics:
            topics = runner.get_topic_names()
            if topics:
                log.info(f"\n📋 Topics in config ({len(topics)}):")
                for i, name in enumerate(topics, 1):
                    log.info(f"  {i}. {name}")
            else:
                log.info("No topics found in config")
            return

        if args.schedule:
            from src.scheduler import run_scheduler

            log.info(f"Starting scheduler with config: {args.config}")
            run_scheduler(args.config)
            return

        # Run specific topic from config
        if args.topic_name:
            # Find the topic by name
            topic = None
            for t in runner.topics:
                if t.get("name", "").lower() == args.topic_name.lower():
                    topic = t
                    break

            if topic:
                log.info(f"🚀 Running topic from config: '{topic.get('name')}'")
                result = runner.run_topic(topic)
                if result.get("status") == "success":
                    log.info(f"✅ Completed: {topic.get('name')}")
                else:
                    log.error(f"❌ Failed: {topic.get('name')}")
            else:
                log.error(f"Topic not found: '{args.topic_name}'")
                log.info("Available topics:")
                for t in runner.get_topic_names():
                    log.info(f"  - {t}")
            return

        # Run all topics
        log.info(f"🚀 Running all topics from: {args.config}")

        if args.limit:
            runner.topics = runner.topics[: args.limit]
            log.info(f"⚠️ Limiting to {args.limit} topic(s)")

        results = runner.run_all()

        success_count = sum(1 for r in results if r["result"].get("status") == "success")
        log.info(f"\n{'=' * 60}")
        log.info(f"📊 Summary: {success_count}/{len(results)} topics completed successfully")
        log.info(f"{'=' * 60}")
        return

    # No arguments
    log.info("""
╔══════════════════════════════════════════════════════════════╗
║                    COMPETITORINTEL                           ║
║         AI-Powered Competitive Intelligence                  ║
╚══════════════════════════════════════════════════════════════╝

Usage:
  # Quick research on any topic
  python main.py --topic "AI customer service tools"

  # Run a specific topic from config
  python main.py --topic-name "AI Customer Service Tools"

  # Run all topics from config
  python main.py --config topics.yaml

  # List topics in config
  python main.py --list-topics

For help:
  python main.py --help
    """)


def create_sample_config():
    """Create a sample config file."""
    sample = """# topics.yaml
# Sample configuration for CompetitorIntel

topics:
  - name: "AI Customer Service Tools"
    description: "Research and analyze AI customer service tools market"
    search_terms:
      - "AI customer service tools 2026"
      - "best AI chatbot for customer service"
      - "AI customer support market trends"
    schedule: "weekly"
    email: "your_email@example.com"

  - name: "Competitor Intel"
    description: "Monitor key competitors in your industry"
    search_terms:
      - "company announcements"
      - "industry trends"
    schedule: "daily"
"""
    with open("topics.yaml", "w") as f:
        f.write(sample.strip())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        log.error(f"❌ Error: {e}")
        sys.exit(1)
