"""Configuration settings for the FastAPI application.

This module centralizes all environment-based and static configuration
to maintain consistency and enable easy deployment across environments.

Configuration can be loaded from environment variables, .env file, or config.yaml.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables, .env file, or config.yaml."""

    # Application metadata
    app_name: str = "AI NARAGI Chat API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server configuration
    server_host: str = "127.0.0.1"
    server_port: int = 8000

    # CORS configuration - origins allowed to access the API
    cors_origins: List[str] = [
        "http://localhost:3000",      # Next.js development server
        "http://127.0.0.1:3000",
        "http://localhost:5173",      # Vite development server (alternative)
        "http://127.0.0.1:5173",
    ]

    # Logging configuration
    log_level: str = "INFO"

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_settings_from_config_loader(config_loader) -> Settings:
    """Load Settings from ConfigLoader instance.
    
    Args:
        config_loader: ConfigLoader instance from llm_core.utils.config_manager
    
    Returns:
        Settings instance with values from config.yaml
    """
    try:
        server_config = config_loader.get_parameter("server")
        
        settings = Settings(
            app_name=server_config.get("app_name", "AI NARAGI Chat API"),
            app_version=server_config.get("app_version", "1.0.0"),
            debug=server_config.get("debug", False),
            server_host=server_config.get("host", "127.0.0.1"),
            server_port=server_config.get("port", 8000),
            cors_origins=server_config.get("cors_origins", [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]),
            log_level=server_config.get("log_level", "INFO"),
        )
        return settings
    except Exception as e:
        # Fallback to default settings if config_loader fails
        return Settings()


# Global settings instance (uses environment variables by default)
settings = Settings()