#!/usr/bin/env python
# main.py
# ============================================
# COMPETITORINTEL - CLI Entry Point
# ============================================
#
# Usage:
#   python main.py --topic "AI customer service tools"
#   python main.py --config topics.yaml
#   python main.py --list-topics
# ============================================

import argparse
import os
import sys

from src.runner import TopicRunner, run_single_topic
from src.utils.logger import log


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CompetitorIntel - AI-powered competitive intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --topic "AI customer service tools"
  python main.py --config topics.yaml
  python main.py --list-topics
  python main.py --config topics.yaml --limit 2
        """,
    )

    parser.add_argument("--topic", "-t", type=str, help="Single topic to research")

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

    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="reports",
        help="Output directory for reports (default: reports)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Set log level
    if args.verbose:
        os.environ["LOG_LEVEL"] = "DEBUG"

    # Single topic mode
    if args.topic:
        log.info(f"🚀 Running research on: '{args.topic}'")
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

        # Load and run topics
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

        # Run all topics
        log.info(f"🚀 Running all topics from: {args.config}")

        # If limit is specified, only run first N
        if args.limit:
            runner.topics = runner.topics[: args.limit]
            log.info(f"⚠️ Limiting to {args.limit} topic(s)")

        results = runner.run_all()

        # Summary
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
  python main.py --topic "AI customer service tools"
  python main.py --config topics.yaml
  python main.py --list-topics

For help:
  python main.py --help
    """)


def create_sample_config():
    """Create a sample config file."""
    sample = """
# topics.yaml
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

  - name: "Industry Trends"
    description: "Latest trends in your industry"
    search_terms:
      - "industry trends 2026"
      - "market analysis"
    schedule: "weekly"
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
