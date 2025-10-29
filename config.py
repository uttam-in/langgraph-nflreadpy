"""
Configuration Management for NFL Player Performance Chatbot.

This module provides centralized configuration management for the application,
loading settings from environment variables with sensible defaults.

Requirements addressed:
- 4.1: Configure data source access and priorities
- 4.2: Configure data source timeouts and retry logic
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API."""
    
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4"))
    temperature: float = field(default_factory=lambda: float(os.getenv("OPENAI_TEMPERATURE", "0.7")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("OPENAI_MAX_TOKENS", "2000")))
    timeout: int = field(default_factory=lambda: int(os.getenv("OPENAI_TIMEOUT", "60")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("OPENAI_MAX_RETRIES", "3")))
    
    def validate(self) -> None:
        """Validate OpenAI configuration."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("OPENAI_TEMPERATURE must be between 0 and 2")
        if self.max_tokens < 1:
            raise ValueError("OPENAI_MAX_TOKENS must be positive")


@dataclass
class DataSourceConfig:
    """Configuration for data sources."""
    
    # Data source priorities (lower number = higher priority)
    # Requirements 4.1: Configure data source priorities
    kaggle_priority: int = field(default_factory=lambda: int(os.getenv("KAGGLE_PRIORITY", "2")))
    nflreadpy_priority: int = field(default_factory=lambda: int(os.getenv("NFLREADPY_PRIORITY", "1")))
    espn_priority: int = field(default_factory=lambda: int(os.getenv("ESPN_PRIORITY", "3")))
    
    # Kaggle dataset configuration
    kaggle_dataset_path: str = field(
        default_factory=lambda: os.getenv("KAGGLE_DATASET_PATH", "./data/nfl_player_stats.csv")
    )
    kaggle_data_path: str = field(
        default_factory=lambda: os.getenv("KAGGLE_DATA_PATH", "./data/kaggle")
    )
    
    # Timeouts (in seconds)
    # Requirements 4.2: Configure timeouts
    kaggle_timeout: int = field(default_factory=lambda: int(os.getenv("KAGGLE_TIMEOUT", "30")))
    nflreadpy_timeout: int = field(default_factory=lambda: int(os.getenv("NFLREADPY_TIMEOUT", "30")))
    espn_timeout: int = field(default_factory=lambda: int(os.getenv("ESPN_API_TIMEOUT", "10")))
    
    # Retry configuration
    # Requirements 4.2: Configure retry logic
    max_retries: int = field(default_factory=lambda: int(os.getenv("DATA_SOURCE_MAX_RETRIES", "3")))
    retry_delay: float = field(default_factory=lambda: float(os.getenv("DATA_SOURCE_RETRY_DELAY", "1.0")))
    retry_backoff: float = field(default_factory=lambda: float(os.getenv("DATA_SOURCE_RETRY_BACKOFF", "2.0")))
    
    # Fallback configuration
    enable_fallback: bool = field(
        default_factory=lambda: os.getenv("DATA_SOURCE_ENABLE_FALLBACK", "true").lower() == "true"
    )
    
    def get_priority_order(self) -> List[str]:
        """
        Get data sources in priority order.
        
        Returns:
            List of data source names ordered by priority (highest first)
            
        Requirements:
            - 4.1: Return data sources in configured priority order
        """
        sources = [
            ("kaggle", self.kaggle_priority),
            ("nflreadpy", self.nflreadpy_priority),
            ("espn", self.espn_priority)
        ]
        # Sort by priority (lower number = higher priority)
        sources.sort(key=lambda x: x[1])
        return [name for name, _ in sources]
    
    def get_timeout(self, source: str) -> int:
        """
        Get timeout for a specific data source.
        
        Args:
            source: Data source name
            
        Returns:
            Timeout in seconds
        """
        timeouts = {
            "kaggle": self.kaggle_timeout,
            "nflreadpy": self.nflreadpy_timeout,
            "espn": self.espn_timeout
        }
        return timeouts.get(source, 30)


@dataclass
class CacheConfig:
    """Configuration for caching."""
    
    # Kaggle cache configuration
    kaggle_cache_enabled: bool = field(
        default_factory=lambda: os.getenv("KAGGLE_CACHE_ENABLED", "true").lower() == "true"
    )
    warm_kaggle_cache_on_startup: bool = field(
        default_factory=lambda: os.getenv("WARM_KAGGLE_CACHE_ON_STARTUP", "true").lower() == "true"
    )
    
    # nflreadpy cache configuration
    nflreadpy_cache_ttl_hours: int = field(
        default_factory=lambda: int(os.getenv("NFLREADPY_CACHE_TTL_HOURS", "24"))
    )
    
    # Query cache configuration
    query_cache_capacity: int = field(
        default_factory=lambda: int(os.getenv("QUERY_CACHE_CAPACITY", "100"))
    )
    query_cache_ttl_hours: int = field(
        default_factory=lambda: int(os.getenv("QUERY_CACHE_TTL_HOURS", "1"))
    )
    
    # General cache settings
    cache_dir: str = field(default_factory=lambda: os.getenv("CACHE_DIR", "./.cache"))


@dataclass
class MemoryConfig:
    """Configuration for conversation memory."""
    
    max_history_turns: int = field(
        default_factory=lambda: int(os.getenv("MAX_HISTORY_TURNS", "10"))
    )
    max_context_tokens: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))
    )
    include_system_messages: bool = field(
        default_factory=lambda: os.getenv("INCLUDE_SYSTEM_MESSAGES", "false").lower() == "true"
    )


@dataclass
class WorkflowConfig:
    """Configuration for LangGraph workflow."""
    
    max_iterations: int = field(
        default_factory=lambda: int(os.getenv("WORKFLOW_MAX_ITERATIONS", "10"))
    )
    timeout: int = field(
        default_factory=lambda: int(os.getenv("WORKFLOW_TIMEOUT", "120"))
    )
    enable_streaming: bool = field(
        default_factory=lambda: os.getenv("WORKFLOW_ENABLE_STREAMING", "true").lower() == "true"
    )
    enable_debug: bool = field(
        default_factory=lambda: os.getenv("WORKFLOW_DEBUG", "false").lower() == "true"
    )


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: Optional[str] = field(default_factory=lambda: os.getenv("LOG_FILE"))
    log_dir: str = field(default_factory=lambda: os.getenv("LOG_DIR", "logs"))
    log_console: bool = field(
        default_factory=lambda: os.getenv("LOG_CONSOLE", "true").lower() == "true"
    )
    log_detailed: bool = field(
        default_factory=lambda: os.getenv("LOG_DETAILED", "false").lower() == "true"
    )
    
    # Component-specific log levels
    workflow_log_level: str = field(
        default_factory=lambda: os.getenv("WORKFLOW_LOG_LEVEL", "INFO")
    )
    nodes_log_level: str = field(
        default_factory=lambda: os.getenv("NODES_LOG_LEVEL", "INFO")
    )
    data_sources_log_level: str = field(
        default_factory=lambda: os.getenv("DATA_SOURCES_LOG_LEVEL", "INFO")
    )


@dataclass
class ChainlitConfig:
    """Configuration for Chainlit interface."""
    
    port: int = field(default_factory=lambda: int(os.getenv("CHAINLIT_PORT", "8000")))
    host: str = field(default_factory=lambda: os.getenv("CHAINLIT_HOST", "0.0.0.0"))
    enable_telemetry: bool = field(
        default_factory=lambda: os.getenv("CHAINLIT_ENABLE_TELEMETRY", "false").lower() == "true"
    )
    session_timeout: int = field(
        default_factory=lambda: int(os.getenv("CHAINLIT_SESSION_TIMEOUT", "3600"))
    )


@dataclass
class AppConfig:
    """Main application configuration."""
    
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    data_sources: DataSourceConfig = field(default_factory=DataSourceConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    chainlit: ChainlitConfig = field(default_factory=ChainlitConfig)
    
    # Application metadata
    app_name: str = "NFL Player Performance Chatbot"
    app_version: str = "1.0.0"
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    
    def validate(self) -> None:
        """
        Validate all configuration settings.
        
        Raises:
            ValueError: If any configuration is invalid
        """
        # Validate OpenAI config
        self.openai.validate()
        
        # Validate data source priorities are unique
        priorities = [
            self.data_sources.kaggle_priority,
            self.data_sources.nflreadpy_priority,
            self.data_sources.espn_priority
        ]
        if len(priorities) != len(set(priorities)):
            raise ValueError("Data source priorities must be unique")
        
        # Validate cache settings
        if self.cache.query_cache_capacity < 1:
            raise ValueError("QUERY_CACHE_CAPACITY must be positive")
        if self.cache.nflreadpy_cache_ttl_hours < 1:
            raise ValueError("NFLREADPY_CACHE_TTL_HOURS must be positive")
        
        # Validate memory settings
        if self.memory.max_history_turns < 1:
            raise ValueError("MAX_HISTORY_TURNS must be positive")
        
        # Validate workflow settings
        if self.workflow.max_iterations < 1:
            raise ValueError("WORKFLOW_MAX_ITERATIONS must be positive")
        if self.workflow.timeout < 1:
            raise ValueError("WORKFLOW_TIMEOUT must be positive")
        
        # Validate logging level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.log_level.upper() not in valid_log_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_log_levels}")
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def get_data_dir(self) -> Path:
        """Get data directory path."""
        return Path(self.data_sources.kaggle_data_path).parent
    
    def get_cache_dir(self) -> Path:
        """Get cache directory path."""
        return Path(self.cache.cache_dir)
    
    def get_log_dir(self) -> Path:
        """Get log directory path."""
        return Path(self.logging.log_dir)
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.get_data_dir(),
            self.get_cache_dir(),
            self.get_log_dir()
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the global application configuration.
    
    Returns:
        AppConfig instance
        
    Note:
        Configuration is loaded once and cached. Call reload_config() to reload.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def load_config() -> AppConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        AppConfig instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    config = AppConfig()
    config.validate()
    config.ensure_directories()
    return config


def reload_config() -> AppConfig:
    """
    Reload configuration from environment variables.
    
    Returns:
        AppConfig instance
    """
    global _config
    _config = load_config()
    return _config


def print_config(config: Optional[AppConfig] = None) -> None:
    """
    Print configuration settings (for debugging).
    
    Args:
        config: Configuration to print (uses global config if None)
    """
    if config is None:
        config = get_config()
    
    print("=" * 80)
    print(f"{config.app_name} v{config.app_version}")
    print(f"Environment: {config.environment}")
    print("=" * 80)
    
    print("\n[OpenAI Configuration]")
    print(f"  Model: {config.openai.model}")
    print(f"  Temperature: {config.openai.temperature}")
    print(f"  Max Tokens: {config.openai.max_tokens}")
    print(f"  Timeout: {config.openai.timeout}s")
    print(f"  Max Retries: {config.openai.max_retries}")
    print(f"  API Key: {'*' * 20 if config.openai.api_key else 'NOT SET'}")
    
    print("\n[Data Source Configuration]")
    print(f"  Priority Order: {config.data_sources.get_priority_order()}")
    print(f"  Kaggle Timeout: {config.data_sources.kaggle_timeout}s")
    print(f"  NFLReadPy Timeout: {config.data_sources.nflreadpy_timeout}s")
    print(f"  ESPN Timeout: {config.data_sources.espn_timeout}s")
    print(f"  Max Retries: {config.data_sources.max_retries}")
    print(f"  Retry Delay: {config.data_sources.retry_delay}s")
    print(f"  Retry Backoff: {config.data_sources.retry_backoff}x")
    print(f"  Enable Fallback: {config.data_sources.enable_fallback}")
    
    print("\n[Cache Configuration]")
    print(f"  Kaggle Cache Enabled: {config.cache.kaggle_cache_enabled}")
    print(f"  Warm Cache on Startup: {config.cache.warm_kaggle_cache_on_startup}")
    print(f"  NFLReadPy Cache TTL: {config.cache.nflreadpy_cache_ttl_hours}h")
    print(f"  Query Cache Capacity: {config.cache.query_cache_capacity}")
    print(f"  Query Cache TTL: {config.cache.query_cache_ttl_hours}h")
    print(f"  Cache Directory: {config.cache.cache_dir}")
    
    print("\n[Memory Configuration]")
    print(f"  Max History Turns: {config.memory.max_history_turns}")
    print(f"  Max Context Tokens: {config.memory.max_context_tokens}")
    print(f"  Include System Messages: {config.memory.include_system_messages}")
    
    print("\n[Workflow Configuration]")
    print(f"  Max Iterations: {config.workflow.max_iterations}")
    print(f"  Timeout: {config.workflow.timeout}s")
    print(f"  Enable Streaming: {config.workflow.enable_streaming}")
    print(f"  Enable Debug: {config.workflow.enable_debug}")
    
    print("\n[Logging Configuration]")
    print(f"  Log Level: {config.logging.log_level}")
    print(f"  Log Directory: {config.logging.log_dir}")
    print(f"  Console Output: {config.logging.log_console}")
    print(f"  Detailed Format: {config.logging.log_detailed}")
    
    print("\n[Chainlit Configuration]")
    print(f"  Host: {config.chainlit.host}")
    print(f"  Port: {config.chainlit.port}")
    print(f"  Session Timeout: {config.chainlit.session_timeout}s")
    
    print("=" * 80)


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        print_config(config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
