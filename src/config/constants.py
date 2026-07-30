# src/config/constants.py
# ============================================
# COMPETITORINTEL - Constants
# ============================================


class AgentLimits:
    """Centralized limits for all agents."""

    # Orchestrator
    ORCHESTRATOR_MAX_STEPS = 10

    # Researcher
    RESEARCHER_MAX_STEPS = 10

    # Analyst
    ANALYST_MAX_STEPS = 10

    # Writer
    WRITER_MAX_STEPS = 15

    # Topic Runner
    RUNNER_MAX_STEPS = 10

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
