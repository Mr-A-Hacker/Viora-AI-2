"""
Settings manager for Viora AI backend.
Centralized settings management with support for environment variables, settings file, and runtime overrides.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_SETTINGS = {
    # Ollama configuration
    "ollama": {
        "enabled": False,
        "model": "gemma2:2b",
        "url": "http://localhost:11434",
        "timeout": 30,
        "max_tokens": 512,
    },
    # Whisper (speech-to-text) configuration
    "whisper": {
        "enabled": True,
        "model": "whisper",
    },
    # Vosk (speech-to-text) configuration
    "vosk": {
        "enabled": False,
        "model": os.path.join(os.environ.get("LOCAL_DIR", "./models"), "vosk-model-small-en-us-0.15"),
    },
    # Backend configuration
    "backend": {
        "model": "qwen2.5-1.5b-instruct-q4_k_m",
        "tools": "functiongemma-pocket-q4_k_m.gguf",
        "use_thinking": True,
        "thinking_temp": 0.4,
        "non_thinking_temp": 0.5,
    },
    # Model file paths
    "paths": {
        "models_dir": os.environ.get("LOCAL_DIR", "./models"),
        "conversations_file": os.environ.get("CONVERSATIONS_FILE", "conversations.json"),
        "tools_file": os.environ.get("TOOLS_PATH", "tools.json"),
        "jobs_file": os.environ.get("JOBS_FILE", "task_jobs.json"),
        "captures_dir": os.environ.get("CAPTURES_DIR", "captures"),
    },
    # Server configuration
    "server": {
        "port": int(os.environ.get("PORT", "8000")),
        "host": "0.0.0.0",
    },
    # UI configuration
    "ui": {
        "auto_reconnect": True,
        "show_advanced_options": False,
        "enable_voice_control": True,
    },
}

# Environment variable mapping
ENV_VAR_MAPPING = {
    "USE_OLLAMA": ("ollama", "enabled"),
    "USE_WHISPER": ("whisper", "enabled"),
    "USE_VOSK": ("vosk", "enabled"),
    "VOSK_MODEL": ("vosk", "model"),
    "OLLAMA_MODEL": ("ollama", "model"),
    "OLLAMA_URL": ("ollama", "url"),
    "OLLAMA_TIMEOUT": ("ollama", "timeout"),
    "OLLAMA_MAX_TOKENS": ("ollama", "max_tokens"),
}

# Public configuration variables for backward compatibility
USE_OLLAMA = os.environ.get("USE_OLLAMA", "false").lower() == "true"
USE_WHISPER = os.environ.get("USE_WHISPER", "true").lower() == "true"
USE_VOSK = os.environ.get("USE_VOSK", "false").lower() == "true"
VOSK_MODEL = os.environ.get("VOSK_MODEL", os.path.join(os.environ.get("LOCAL_DIR", "./models"), "vosk-model-small-en-us-0.15"))
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2:2b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "30"))
OLLAMA_MAX_TOKENS = int(os.environ.get("OLLAMA_MAX_TOKENS", "512"))


def _load_from_env_to_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Load settings from environment variables."""
    updated_settings = settings.copy()
    
    for env_var, (section, key) in ENV_VAR_MAPPING.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            try:
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                elif value.isdigit():
                    if section == "ollama" and (key == "timeout" or key == "max_tokens"):
                        value = int(value)
                    elif key == "port":
                        value = int(value)
            except (ValueError, TypeError):
                pass
            
            if section not in updated_settings:
                updated_settings[section] = {}
            updated_settings[section][key] = value
    
    return updated_settings

def get_settings():
    """Get current settings from environment and settings file."""
    # Start with default settings
    settings = DEFAULT_SETTINGS.copy()
    
    # Load from environment variables (override defaults)
    settings = _load_from_env_to_settings(settings)
    
    # Load from settings file if exists (override environment)
    settings_file = Path(__file__).resolve().parent / "settings.json"
    if settings_file.exists():
        try:
            with open(settings_file, "r") as f:
                file_settings = json.load(f)
            
            # Merge file settings (they take precedence)
            def merge_dicts(a, b):
                result = a.copy()
                for key, value in b.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = merge_dicts(result[key], value)
                    else:
                        result[key] = value
                return result
            
            settings = merge_dicts(settings, file_settings)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load settings from file: {e}")
    
    return settings

def save_settings(settings: Dict[str, Any]):
    """Save settings to the settings file."""
    try:
        settings_file = Path(__file__).resolve().parent / "settings.json"
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
        logger.info(f"Settings saved to {settings_file}")
        return True
    except IOError as e:
        logger.error(f"Failed to save settings: {e}")
        return False

def get_setting(key_path: str, default: Any = None):
    """Get a specific setting by dot-separated path."""
    settings = get_settings()
    keys = key_path.split(".")
    current = settings
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current

def set_setting(key_path: str, value: Any, save: bool = True):
    """Set a specific setting by dot-separated path."""
    settings = get_settings()
    keys = key_path.split(".")
    current = settings
    
    for i, key in enumerate(keys[:-1]):
        next_key = keys[i + 1]
        if isinstance(current, dict):
            if key not in current:
                current[key] = {}
            current = current[key]
        else:
            return False
    
    if isinstance(current, dict):
        current[keys[-1]] = value
        if save:
            save_settings(settings)
        return True
    return False

def is_ollama_enabled():
    """Check if Ollama integration is enabled."""
    return get_setting("ollama.enabled", False)

def toggle_ollama(enabled: bool = None, save: bool = True):
    """Enable or disable Ollama integration.
    
    Args:
        enabled: New state, if None, toggle current state
        save: Whether to save the change to file
        
    Returns:
        True if successful, False otherwise
    """
    current = get_setting("ollama.enabled", False)
    if enabled is None:
        enabled = not current
    
    if set_setting("ollama.enabled", enabled, save):
        global USE_OLLAMA
        USE_OLLAMA = enabled
        return True
    return False

def get_model_config():
    """Get model configuration based on current settings."""
    settings = get_settings()
    
    if settings.get("ollama", {}).get("enabled", False):
        # Use Ollama
        return {
            "use_ollama": True,
            "ollama_url": settings.get("ollama", {}).get("url", "http://localhost:11434"),
            "ollama_model": settings.get("ollama", {}).get("model", "gemma2:2b"),
            "ollama_timeout": settings.get("ollama", {}).get("timeout", 30),
            "ollama_max_tokens": settings.get("ollama", {}).get("max_tokens", 512),
            "fallback_qwen": False,
        }
    else:
        # Use Qwen + Function Gemma (original setup)
        return {
            "use_ollama": False,
            "qwen_model_path": os.path.join(
                settings.get("paths", {}).get("models_dir", "./models"),
                "qwen2", settings.get("backend", {}).get("model", "qwen2.5-1.5b-instruct-q4_k_m") + ".gguf"
            ),
            "tool_model_path": os.path.join(
                settings.get("paths", {}).get("models_dir", "./models"),
                settings.get("backend", {}).get("tools", "functiongemma-pocket-q4_k_m.gguf")
            ),
            "use_whisper": settings.get("whisper", {}).get("enabled", True),
            "use_vosk": settings.get("vosk", {}).get("enabled", False),
            "vosk_model": settings.get("vosk", {}).get("model", os.path.join(os.environ.get("LOCAL_DIR", "./models"), "vosk-model-small-en-us-0.15")),
            "use_thinking": settings.get("backend", {}).get("use_thinking", True),
            "thinking_temp": settings.get("backend", {}).get("thinking_temp", 0.4),
            "non_thinking_temp": settings.get("backend", {}).get("non_thinking_temp", 0.5),
            "fallback_qwen": not settings.get("whisper", {}).get("enabled", True) and not settings.get("vosk", {}).get("enabled", False),
        }


def setup_logging():
    """Configure logging with configurable level."""
    from config import LOG_LEVEL
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger()
    if LOG_LEVEL:
        try:
            fh = logging.FileHandler(LOG_LEVEL, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
            logger.addHandler(fh)
        except OSError:
            logger.warning("Could not open log file %s", LOG_LEVEL)


if __name__ == "__main__":
    print("Viora AI Settings")
    print("=" * 50)
    
    settings = get_settings()
    
    print(f"Ollama enabled: {get_setting('ollama.enabled', False)}")
    print(f"Model: {get_setting('ollama.model', 'not set')}")
    print(f"Whisper enabled: {get_setting('whisper.enabled', True)}")
    print(f"Vosk enabled: {get_setting('vosk.enabled', False)}")
    
    print("\nCommands:")
    print("1. toggle_ollama [true|false] - Enable/disable Ollama")
    print("2. save - Save current settings")
    print("3. load <filename> - Load settings from file")
    print("4. show - Show current settings")
    print("5. exit - Exit")
    
    while True:
        try:
            cmd = input("\n> ").strip()
            if not cmd:
                continue
                
            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            
            if action == "toggle_ollama":
                if len(parts) > 1:
                    enabled = parts[1].lower() in ("true", "1", "yes", "on")
                    if toggle_ollama(enabled):
                        print(f"Ollama {'enabled' if enabled else 'disabled'}.")
                    else:
                        print("Failed to toggle Ollama.")
                else:
                    if toggle_ollama():
                        print(f"Ollama {'enabled' if get_setting('ollama.enabled', False) else 'disabled'}.")
                    else:
                        print("Failed to toggle Ollama.")
            elif action == "save":
                current_settings = get_settings()
                if save_settings(current_settings):
                    print("Settings saved.")
                else:
                    print("Failed to save settings.")
            elif action == "show":
                print("\nCurrent settings:")
                print(json.dumps(get_settings(), indent=2))
            elif action == "exit":
                break
            else:
                print(f"Unknown command: {action}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
