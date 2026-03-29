"""
Elite Dangerous AI NPC Integration System

This package provides AI-powered NPCs that react intelligently to player actions,
galactic events, and current game state in Elite Dangerous.

Key Components:
- NPCFilter: Determines what data matters to each NPC and their sentiment about it
- ContextBuilder: Assembles filtered data into rich conversation prompts
- AIService: Interfaces with various AI providers (OpenAI, Anthropic, local models)
- TestRunner: Test the system with constructed data before deploying

Usage:
    from ai_integration import TestRunner, create_openai_config, NPCType
    
    # Basic testing without AI
    runner = TestRunner()
    runner.run_full_test_suite("Test Trader")
    
    # Testing with AI (requires API key)
    config = create_openai_config("your-api-key")
    runner = TestRunner(config)
    runner.run_full_test_suite("Test Trader", "Hello there!")
"""

# Core components
from .models import (
    PlayerAction, PlayerStatus, SystemState, GalacticNews, NPCPersonality,
    EventType, NPCType, FilteredData, ConversationContext
)

from .npc_filter import NPCFilter

from .context_builder import ContextBuilder

from .ai_service import (
    AIService, AIConfig, AIProvider, AIResponse,
    create_openai_config, create_anthropic_config, create_local_config
)

from .test_runner import TestRunner

from .config import SystemConfig, DEFAULT_ED_PATHS, NPC_PRESETS, AI_MODEL_RECOMMENDATIONS

# Version info
__version__ = "0.1.0"
__author__ = "Elite Dangerous AI NPC Project"

# Quick setup functions
def quick_test(npc_type: str = "trader", ai_api_key: str = None, ai_provider: str = "openai"):
    """
    Quick test function for immediate results.
    
    Args:
        npc_type: Type of NPC to test ("trader", "pirate", "explorer")
        ai_api_key: API key for AI service (optional)
        ai_provider: AI provider ("openai", "anthropic", "local")
    
    Returns:
        Test results dictionary
    """
    runner = TestRunner()
    
    if ai_api_key:
        if ai_provider.lower() == "openai":
            config = create_openai_config(ai_api_key)
        elif ai_provider.lower() == "anthropic":
            config = create_anthropic_config(ai_api_key)
        else:
            config = create_local_config()
        
        runner.set_ai_config(config)
    
    npc_name_map = {
        "trader": "Test Trader",
        "pirate": "Test Pirate", 
        "explorer": "Test Explorer"
    }
    
    npc_name = npc_name_map.get(npc_type.lower(), "Test Trader")
    return runner.run_full_test_suite(npc_name)


def create_custom_npc_scenario(
    npc_name: str,
    npc_type: NPCType,
    background: str,
    player_actions: list = None,
    system_name: str = "Test System",
    security_level: str = "Medium"
):
    """
    Create a custom testing scenario.
    
    Args:
        npc_name: Name for the custom NPC
        npc_type: NPCType enum value
        background: Background story for the NPC
        player_actions: List of player action dictionaries
        system_name: Name of the star system
        security_level: Security level of the system
    
    Returns:
        Configured TestRunner instance
    """
    runner = TestRunner()
    
    # Create custom NPC
    runner.create_custom_npc_test(npc_name, npc_type, background)
    
    # Modify scenario if custom data provided
    if player_actions or system_name != "Test System":
        runner.modify_sample_data(
            player_actions=player_actions,
            system_info={
                "name": system_name,
                "security_level": security_level
            }
        )
    
    return runner


# Convenience exports for common use cases
__all__ = [
    # Core classes
    "NPCFilter",
    "ContextBuilder", 
    "AIService",
    "TestRunner",
    
    # Data models
    "PlayerAction",
    "PlayerStatus",
    "SystemState",
    "GalacticNews",
    "NPCPersonality",
    "ConversationContext",
    
    # Enums
    "EventType",
    "NPCType",
    "AIProvider",
    
    # Configuration
    "SystemConfig",
    "AIConfig",
    "DEFAULT_ED_PATHS",
    "NPC_PRESETS",
    
    # Quick setup functions
    "create_openai_config",
    "create_anthropic_config", 
    "create_local_config",
    "quick_test",
    "create_custom_npc_scenario"
]