# src/config/settings.py
# COMPETITORINTEL - Configuration Settings

from pathlib import Path
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from mypy.nodes import Enum
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings

# LOAD ENVIRONMENT VARIABLES

env_file = Path(".env")
if env_file.exists():
    load_dotenv(env_file)


# Provider Enum
class LLMProvider(str, Enum):
    OLLAMA = ("ollama",)
    GROQ = ("groq",)
    OPENAI = ("openai",)
    OPENROUTER = "openrouter"


# LLM SETTINGS

DEFAULT_MODEL = "qwen2:7b"


class LLMSettings(BaseSettings):
    """Configuration for the LLM client."""

    default_model: str = Field(default=DEFAULT_MODEL, description="default model for most tasks")
    analyst_model: str = Field(default=DEFAULT_MODEL, description="Model for analysis tasks")
    writer_model: str = Field(default=DEFAULT_MODEL, description="Model for writing tasks")
    researcher_model: str = Field(default=DEFAULT_MODEL, description="Model for research tasks")
    orchestrator_model: str = Field(default=DEFAULT_MODEL, description="Model for orchestration")

    provider: LLMProvider = Field(
        default=LLMProvider.OLLAMA, description="LLMProvider to use: groq, ollama or openai"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Controls randomness 0 = deterministic, 1 = creative",
    )
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Maximum tokens in response")
    timeout: int = Field(default=30, ge=5, le=300, description="Timeout in seconds for API calls")
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Number of retries for failed API calls"
    )

    @field_validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError(f"Temperature must be between 0 and 1, got {v}")
        return v


# AGENT SETTINGS


class AgentSettings(BaseSettings):
    """Configuration for agent behavior."""

    max_steps: int = Field(
        default=10, ge=1, le=50, description="max steps an agent can take before stopping"
    )
    max_concurrent_agents: int = Field(
        default=3, ge=1, le=10, description="Max agents running simultaneously"
    )
    enable_validation: bool = Field(default=True, description="Validate all inputs and outputs")
    enable_guardrails: bool = Field(
        default=True, description="enable safety guardrails for agent actions"
    )
    task_timeout: int = Field(
        default=300, ge=10, le=3600, description="max seconds for a complete task"
    )
    step_timeout: int = Field(default=60, ge=5, le=300, description="Max seconds for a single step")


# TOOL SETTINGS


class ToolSettings(BaseSettings):
    """Configuration for tools."""

    search_max_results: int = Field(
        default=10, ge=1, le=50, description="Maximum results to return from a search."
    )
    search_timeout: int = Field(
        default=30, ge=5, le=120, description="Timeout for search API calls."
    )
    scrape_max_pages: int = Field(
        default=5, ge=1, le=20, description="Maximum pages to scrape per search result."
    )
    scrape_timeout: int = Field(default=30, ge=5, le=120, description="Timeout for scraping.")
    report_max_sections: int = Field(
        default=10, ge=1, le=20, description="Maximum sections in a report."
    )
    report_format: Literal["markdown", "html", "json"] = Field(
        default="markdown", description="Format for reports."
    )


# MEMORY SETTINGS


class MemorySettings(BaseSettings):
    """Configuration for the memory system."""

    enabled: bool = Field(default=True, description="Enable memory system.")
    short_term_max_entries: int = Field(
        default=100, ge=1, le=1000, description="Maximum short-term memory entries."
    )
    long_term_max_entries: int = Field(
        default=1000, ge=1, le=10000, description="Maximum long-term memory entries."
    )
    retention_days: int = Field(
        default=30, ge=1, le=365, description="Days to keep memory entries."
    )


# MAIN SETTINGS CLASS


class Settings(BaseSettings):
    """
    Main configuration for CompetitorIntel.

    WHY: Single entry point for ALL configuration.
    WHY: Everything validates on load.
    """

    # API KEYS
    openai_api_key: SecretStr | None = Field(
        default=None, validation_alias="OPENAI_API_KEY", description="OpenAI API key for LLM calls."
    )

    groq_api_key: SecretStr | None = Field(
        default=None, validation_alias="GROQ_API_KEY", description="Groq API key for LLM calls."
    )

    openrouter_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENROUTER_API_KEY",
        description="OpenRouter API key for LLM calls.",
    )

    tavily_api_key: Optional[SecretStr] = Field(
        default=None, validation_alias="TAVILY_API_KEY", description="Tavily API key for search."
    )

    google_search_api_key: Optional[SecretStr] = Field(
        default=None, validation_alias="GOOGLE_SEARCH_API_KEY", description="Google Search API key."
    )

    google_search_engine_id: Optional[str] = Field(
        default=None,
        validation_alias="GOOGLE_SEARCH_ENGINE_ID",
        description="Google Search Engine ID.",
    )

    # SYSTEM SETTINGS

    debug: bool = Field(default=False, validation_alias="DEBUG", description="Debug mode.")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", validation_alias="LOG_LEVEL", description="Logging level."
    )

    environment: Literal["dev", "staging", "production"] = Field(
        default="dev", validation_alias="ENVIRONMENT", description="Environment name."
    )

    # NESTED SETTINGS

    llm: LLMSettings = Field(default_factory=LLMSettings, description="LLM configuration.")
    agent: AgentSettings = Field(default_factory=AgentSettings, description="Agent configuration.")
    tool: ToolSettings = Field(default_factory=ToolSettings, description="Tool configuration.")
    memory: MemorySettings = Field(
        default_factory=MemorySettings, description="Memory configuration."
    )

    # VALIDATORS
    @field_validator("environment")
    def validate_environment(cls, v: str) -> str:
        if v not in ["dev", "staging", "production"]:
            raise ValueError(f"Environment must be 'dev', 'staging', or 'production', got {v}")
        return v

    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}, got {v}")
        return v

    # POST-VALIDATION

    def model_post_init(self, __context: Any) -> None:
        """Check required fields after initialization.
        diff providers need diff openai key
        """
        provider = self.llm.provider
        if provider == LLMProvider.OPENAI:
            if self.openai_api_key is None:
                raise ValueError(
                    "OPENAI_API_KEY is required but not found in environment variables.\n"
                    "Please add it to your .env file: OPENAI_API_KEY=sk-... \n"
                    "Or switch to Ollama: set llm.provider = 'ollama'"
                )
            elif provider == LLMProvider.GROQ:
                if self.groq_api_key is None:
                    raise ValueError(
                        "GROQ_API_KEY is required when using Groq provider.\n"
                        "Please add it to your .env file: GROQ_API_KEY=gsk_...\n"
                        "Or switch to Ollama: set llm.provider = 'ollama'"
                    )
            elif provider == LLMProvider.OLLAMA:
                # Ollama doesn't need an API key
                # we just check if Ollama is installed
                pass
            # Check if we have at least one search provider
            has_tavily = self.tavily_api_key is not None
            has_google = (
                self.google_search_api_key is not None and self.google_search_engine_id is not None
            )

            if not has_tavily and not has_google:
                # This is a warning, not an error
                print(
                    "WARNING: No search provider configured.\n"
                    "Please add TAVILY_API_KEY or GOOGLE_SEARCH_API_KEY to your .env file."
                )

    # HELPER METHODS
    def is_production(self) -> bool:
        return self.environment == "production"

    def is_dev(self) -> bool:
        return self.environment == "dev"

    def get_model_for_task(self, task_type: str) -> str:
        model_map = {
            "default": self.llm.default_model,
            "analyst": self.llm.analyst_model,
            "writer": self.llm.writer_model,
            "researcher": self.llm.researcher_model,
            "orchestrator": self.llm.orchestrator_model,
        }
        return model_map.get(task_type, self.llm.default_model)

    def get_provider(self) -> LLMProvider:
        """Get the current LLM provider"""
        return self.llm.provider


# CREATE SINGLETON INSTANCE

settings = Settings()

# TEST CODE

if __name__ == "__main__":
    print("=" * 60)
    print("CompetitorIntel - Settings Test")
    print("=" * 60)

    print(f"\nProvider: {settings.llm.provider.value}")
    print(f"Default Model: {settings.llm.default_model}")

    # Show API keys (masked)
    if settings.openai_api_key:
        print(f"OpenAI API Key: {settings.openai_api_key.get_secret_value()[:10]}...")
    else:
        print("OpenAI API Key: NOT SET")

    if settings.groq_api_key:
        print(f"Groq API Key: {settings.groq_api_key.get_secret_value()[:10]}...")
    else:
        print("Groq API Key: NOT SET")

    if settings.tavily_api_key:
        print(f"Tavily API Key: {settings.tavily_api_key.get_secret_value()[:10]}...")

    print(f"\nEnvironment: {settings.environment}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Log Level: {settings.log_level}")

    print("\n--- LLM Settings ---")
    print(f"Default Model: {settings.llm.default_model}")
    print(f"Analyst Model: {settings.llm.analyst_model}")
    print(f"Temperature: {settings.llm.temperature}")
    print(f"Max Tokens: {settings.llm.max_tokens}")

    print("\n--- Agent Settings ---")
    print(f"Max Steps: {settings.agent.max_steps}")
    print(f"Task Timeout: {settings.agent.task_timeout}s")

    print("\n--- Tool Settings ---")
    print(f"Search Max Results: {settings.tool.search_max_results}")
    print(f"Report Format: {settings.tool.report_format}")

    print("\n--- Memory Settings ---")
    print(f"Memory Enabled: {settings.memory.enabled}")
    print(f"Short-term Max Entries: {settings.memory.short_term_max_entries}")

    print("\n--- Helper Methods ---")
    print(f"Is Production? {settings.is_production()}")
    print(f"Is Dev? {settings.is_dev()}")
    print(f"Model for analyst: {settings.get_model_for_task('analyst')}")

    print("=" * 60)
    print("Settings loaded successfully!")
