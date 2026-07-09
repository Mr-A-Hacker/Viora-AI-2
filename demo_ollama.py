"""
Ollama Integration Demo for Viora AI.
Demonstrates how to enable/disable Ollama integration and switch between models.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import get_model_config, is_ollama_enabled, toggle_ollama, get_settings, save_settings
from chat_ai import AIState
from tool_ai import preload_tool_model
import logging

def setup_logging():
    """Configure logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def demo_initial_state():
    """Show the initial state of the system."""
    print("=" * 60)
    print("Viora AI Ollama Integration Demo")
    print("=" * 60)
    
    logger = setup_logging()
    
    print("\n1. INITIAL STATE:")
    print(f"   - Ollama enabled: {is_ollama_enabled()}")
    print(f"   - Model config: {get_model_config()}")
    
    # Show settings
    settings = get_settings()
    print(f"\n2. CURRENT SETTINGS:")
    print(f"   - ollama.enabled: {settings['ollama']['enabled']}")
    print(f"   - ollama.model: {settings['ollama']['model']}")
    print(f"   - whisper.enabled: {settings['whisper']['enabled']}")
    print(f"   - backend.use_thinking: {settings['backend']['use_thinking']}")
    
    return logger

def demo_enable_ollama(logger):
    """Enable Ollama integration."""
    print("\n3. ENABLING OLLAMA:")
    logger.info("Enabling Ollama integration...")
    
    # Toggle Ollama to True
    result = toggle_ollama(True)
    print(f"   - Toggle Ollama to: True")
    print(f"   - Success: {result}")
    print(f"   - Is Ollama enabled now: {is_ollama_enabled()}")
    
    # Get the new model config
    model_config = get_model_config()
    print(f"   - Use Ollama: {model_config['use_ollama']}")
    print(f"   - Ollama model: {model_config['ollama_model']}")
    
    # Simulate saving settings (in real scenario, this would trigger model reload)
    settings = get_settings()
    save_settings(settings)
    print(f"   - Settings saved to settings.json")

def demo_disable_ollama(logger):
    """Disable Ollama integration and switch back to default."""
    print("\n4. DISABLING OLLAMA:")
    logger.info("Disabling Ollama integration, switching to default Qwen + Function Gemma...")
    
    # Toggle Ollama to False
    result = toggle_ollama(False)
    print(f"   - Toggle Ollama to: False")
    print(f"   - Success: {result}")
    print(f"   - Is Ollama enabled now: {is_ollama_enabled()}")
    
    # Get the new model config
    model_config = get_model_config()
    print(f"   - Use Ollama: {model_config['use_ollama']}")
    print(f"   - Qwen model path: {model_config['qwen_model_path']}")
    print(f"   - Tool model path: {model_config['tool_model_path']}")
    print(f"   - Use Whisper: {model_config['use_whisper']}")
    
    # Simulate saving settings
    settings = get_settings()
    save_settings(settings)
    print(f"   - Settings saved to settings.json")

def demo_model_selection(logger):
    """Demonstrate model selection and loading."""
    print("\n5. MODEL SELECTION:")
    print("   - Current model configuration:")
    model_config = get_model_config()
    
    if model_config['use_ollama']:
        print(f"     * Ollama model: {model_config['ollama_model']}")
        print(f"     * Ollama URL: {model_config['ollama_url']}")
        print(f"     * Timeout: {model_config['ollama_timeout']}s")
    else:
        print(f"     * Qwen model: {model_config['qwen_model_path']}")
        print(f"     * Tool model: {model_config['tool_model_path']}")
        print(f"     * Whisper enabled: {model_config['use_whisper']}")
        print(f"     * Thinking mode: {model_config['use_thinking']}")
        print(f"     * Thinking temp: {model_config['thinking_temp']}")
        print(f"     * Non-thinking temp: {model_config['non_thinking_temp']}")

def demo_model_reload(logger):
    """Demonstrate model reloading."""
    print("\n6. MODEL RELOAD SIMULATION:")
    print("   - Creating AIState instance...")
    
    # Note: In a real scenario, the model would be loaded here
    # We're simulating the behavior by showing the configuration
    ai_state = AIState()
    print(f"   - AIState created")
    print(f"   - Current model config: {get_model_config()}")
    
    print("\n   - Loading tool model...")
    preload_tool_model()
    print(f"   - Tool model loaded (simulated)")

def show_all_features(logger):
    """Show all available features with Ollama enabled vs disabled."""
    print("\n7. FEATURES COMPARISON:")
    
    settings = get_settings()
    
    # Features when Ollama is enabled
    print(f"\n   WITH OLLAMA ENABLED:")
    print(f"     - Model: {settings['ollama']['model']}")
    print(f"     - URL: {settings['ollama']['url']}")
    print(f"     - Timeout: {settings['ollama']['timeout']}s")
    print(f"     - Max tokens: {settings['ollama']['max_tokens']}")
    print(f"     - Whisper: {settings['whisper']['enabled']} (fallback)")
    print(f"     - Vosk: {settings['vosk']['enabled']}")
    
    # Features when Ollama is disabled
    print(f"\n   WITH OLLAMA DISABLED:")
    print(f"     - Qwen model: {settings['backend']['model']}")
    print(f"     - Function Gemma tools: {settings['backend']['tools']}")
    print(f"     - Whisper: {settings['whisper']['enabled']}")
    print(f"     - Vosk: {settings['vosk']['enabled']}")
    print(f"     - Thinking mode: {settings['backend']['use_thinking']}")
    print(f"     - Thinking temp: {settings['backend']['thinking_temp']}")
    
    print(f"\n   - Both modes support:")
    print(f"     * Chat conversations with full context")
    print(f"     * Voice input (Whisper) and text input")
    print(f"     * Tool/function calling via Function Gemma")
    print(f"     * Semantic routing (Qwen_basic / Qwen_thinking)")

def main():
    """Run the complete demo."""
    try:
        logger = demo_initial_state()
        
        demo_enable_ollama(logger)
        
        demo_model_selection(logger)
        
        demo_model_reload(logger)
        
        demo_disable_ollama(logger)
        
        show_all_features(logger)
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nKey Points:")
        print("1. Ollama integration can be toggled via toggle_ollama()")
        print("2. Settings are persisted to settings.json")
        print("3. Model configuration is loaded from settings")
        print("4. When Ollama is enabled, Qwen models are replaced")
        print("5. When Ollama is disabled, fallback to Qwen + Function Gemma")
        print("\nUsage:")
        print("  - Set USE_OLLAMA=true to enable Ollama at startup")
        print("  - Set USE_OLLAMA=false to use Qwen + Function Gemma")
        print("  - Modify settings in settings.json to customize")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
