# src/config/constants.py
# ============================================
# COMPETITORINTEL - Constants
# ============================================


class AgentLimits:
    """Centralized limits for all agents."""

    # Orchestrator
    ORCHESTRATOR_MAX_STEPS = 5

    # Researcher
    RESEARCHER_MAX_STEPS = 4

    # Analyst
    ANALYST_MAX_STEPS = 6

    # Writer
    WRITER_MAX_STEPS = 8

    # Topic Runner
    RUNNER_MAX_STEPS = 6

    # Search
    SEARCH_MAX_RESULTS = 2


class ReportSettings:
    """Report generation settings."""

    # Minimum report length to be considered meaningful
    MIN_REPORT_LENGTH = 200

    # Output directory
    OUTPUT_DIR = "reports"

    # Email settings
    EMAIL_ENABLED = True

    # Formats to generate
    FORMATS = ["markdown", "html", "pdf"]
