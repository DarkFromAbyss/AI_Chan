"""Configuration management for the LLM core system.

Loads and validates configuration from YAML files.
Centralizes all environment-based settings per rules.md.
Provides ConfigLoader for convenient access to nested configuration values.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from llm_core.utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load and parse YAML configuration file.
    
    Args:
        config_path: Absolute or relative path to config.yaml
    
    Returns:
        Parsed configuration dictionary
    
    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If YAML parsing fails
    
    Example:
        config = load_config("config.yaml")
        data_dir = config["parameters"]["data"]["data_directory"]
    """
    if not os.path.exists(config_path):
        logger.error("Configuration file not found: %s", config_path)
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        logger.info("Configuration loaded successfully from %s", config_path)
        return config
    except yaml.YAMLError as e:
        logger.error("YAML parsing error in %s: %s", config_path, e, exc_info=True)
        raise


def get_model_path(config: Dict[str, Any], model_name: str) -> str:
    """Resolve model path from configuration (legacy support).
    
    Args:
        config: Configuration dictionary from load_config()
        model_name: Model identifier (e.g., "all-MiniLM-L6-v2", "Qwen2.5-7B-Instruct")
    
    Returns:
        Absolute path to model directory
    
    Raises:
        KeyError: If model_name not found in config
        FileNotFoundError: If resolved path does not exist
    
    Example:
        embedding_model_path = get_model_path(config, "all-MiniLM-L6-v2")
    """
    # Support both old and new config structures
    if "parameters" in config and "data" in config["parameters"]:
        models = config["parameters"]["data"].get("models", {})
    elif "models" in config:
        models = config["models"]
    else:
        raise KeyError("'models' key not found in configuration")
    
    if model_name not in models:
        raise KeyError(f"Model '{model_name}' not found in configuration")
    
    model_path = models[model_name]
    
    if not os.path.exists(model_path):
        logger.error("Model path does not exist: %s", model_path)
        raise FileNotFoundError(f"Model not found at: {model_path}")
    
    logger.debug("Resolved model path for '%s': %s", model_name, model_path)
    return model_path


def get_data_directory(config: Dict[str, Any]) -> str:
    """Resolve data directory path from configuration (legacy support).
    
    Args:
        config: Configuration dictionary from load_config()
    
    Returns:
        Absolute path to data directory
    
    Raises:
        KeyError: If data_directory not in config
        FileNotFoundError: If path does not exist
    """
    # Support both old and new config structures
    if "parameters" in config and "data" in config["parameters"]:
        data_dir = config["parameters"]["data"].get("data_directory")
    elif "data_directory" in config:
        data_dir = config.get("data_directory")
    else:
        data_dir = None
    
    if not data_dir:
        raise KeyError("'data_directory' not found in configuration")
    
    if not os.path.exists(data_dir):
        logger.error("Data directory does not exist: %s", data_dir)
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    logger.debug("Data directory resolved: %s", data_dir)
    return data_dir


class ConfigLoader:
    """Unified configuration loader for centralized configuration management.
    
    Provides convenient methods to access paths and parameters from the
    structured config.yaml file. Resolves relative paths to absolute paths.
    
    Example:
        config_loader = ConfigLoader("config.yaml")
        server_port = config_loader.get_parameter("server.port")
        data_dir = config_loader.get_path("data")
        tts_host = config_loader.get_parameter("tts.voicevox_host")
    """
    
    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize ConfigLoader with a configuration file.
        
        Args:
            config_path: Path to config.yaml (absolute or relative)
        
        Raises:
            FileNotFoundError: If config file does not exist
            yaml.YAMLError: If YAML parsing fails
        """
        self.config = load_config(config_path)
        self.config_path = Path(config_path).resolve()
        self.project_root = self.config_path.parent
        logger.debug("ConfigLoader initialized with project root: %s", self.project_root)
    
    def get_path(self, path_key: str) -> Path:
        """Get a resolved absolute path from the paths section.
        
        Args:
            path_key: Key in paths section (e.g., "data", "backend", "models")
        
        Returns:
            Absolute Path object
        
        Raises:
            KeyError: If path_key not found in paths section
        
        Example:
            data_path = config_loader.get_path("data")
            backend_path = config_loader.get_path("backend")
        """
        if "paths" not in self.config:
            raise KeyError("'paths' section not found in configuration")
        
        paths = self.config["paths"]
        
        if path_key not in paths:
            raise KeyError(f"Path key '{path_key}' not found in configuration")
        
        path_value = paths[path_key]
        
        # Resolve relative to project root
        resolved_path = Path(path_value)
        if not resolved_path.is_absolute():
            resolved_path = self.project_root / path_value
        
        logger.debug("Resolved path '%s' to %s", path_key, resolved_path)
        return resolved_path
    
    def get_parameter(self, param_path: str) -> Any:
        """Get a parameter value using dot notation (e.g., "server.port").
        
        Args:
            param_path: Dot-separated path to parameter (e.g., "tts.voicevox_host")
        
        Returns:
            Parameter value of any type
        
        Raises:
            KeyError: If parameter path not found
        
        Example:
            port = config_loader.get_parameter("server.port")
            tts_timeout = config_loader.get_parameter("tts.voicevox_timeout")
            cors_origins = config_loader.get_parameter("server.cors_origins")
        """
        if "parameters" not in self.config:
            raise KeyError("'parameters' section not found in configuration")
        
        keys = param_path.split(".")
        value = self.config["parameters"]
        
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                raise KeyError(f"Parameter path '{param_path}' not found in configuration")
            value = value[key]
        
        logger.debug("Retrieved parameter '%s': %s", param_path, value)
        return value
    
    def get_parameter_safe(self, param_path: str, default: Any = None) -> Any:
        """Get a parameter value with a default fallback.
        
        Args:
            param_path: Dot-separated path to parameter
            default: Default value if parameter not found
        
        Returns:
            Parameter value or default
        
        Example:
            debug = config_loader.get_parameter_safe("server.debug", False)
        """
        try:
            return self.get_parameter(param_path)
        except KeyError:
            logger.debug("Parameter '%s' not found, using default: %s", param_path, default)
            return default
    
    def get_model_path(self, model_name: str) -> Path:
        """Get absolute path to a model directory.
        
        Args:
            model_name: Model identifier (e.g., "all-MiniLM-L6-v2")
        
        Returns:
            Absolute Path to model directory
        
        Raises:
            KeyError: If model not found in configuration
        
        Example:
            embedding_model = config_loader.get_model_path("all-MiniLM-L6-v2")
        """
        model_path_str = self.get_parameter(f"data.models.{model_name}")
        
        resolved_path = Path(model_path_str)
        if not resolved_path.is_absolute():
            resolved_path = self.project_root / model_path_str
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"Model path does not exist: {resolved_path}")
        
        logger.debug("Resolved model '%s' to %s", model_name, resolved_path)
        return resolved_path
    
    def get_data_directory(self) -> Path:
        """Get absolute path to the data directory.
        
        Returns:
            Absolute Path to data directory
        
        Raises:
            KeyError: If data directory not configured
        
        Example:
            data_dir = config_loader.get_data_directory()
        """
        data_path_str = self.get_parameter("data.data_directory")
        
        resolved_path = Path(data_path_str)
        if not resolved_path.is_absolute():
            resolved_path = self.project_root / data_path_str
        
        if not resolved_path.exists():
            raise FileNotFoundError(f"Data directory does not exist: {resolved_path}")
        
        logger.debug("Data directory resolved: %s", resolved_path)
        return resolved_path
    
    def get_brain_path(self) -> Path:
        """Get absolute path to the brain directory with LLM version.
        
        Returns:
            Absolute Path to brain/version directory (e.g., brain/7B)
        
        Raises:
            KeyError: If brain path cannot be constructed
        
        Example:
            brain_dir = config_loader.get_brain_path()
        """
        brain_version = self.get_parameter("llm.brain_version")
        brain_dir = self.get_path("brain")
        brain_path = brain_dir / brain_version
        
        logger.debug("Brain path resolved: %s", brain_path)
        return brain_path
