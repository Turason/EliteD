"""
Configuration settings for the Elite Dangerous AI NPC system.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional
from .ai_service import AIProvider


@dataclass
class SystemConfig:
    """Main system configuration."""
    
    # AI Service Settings
    ai_provider: AIProvider = AIProvider.OPENAI
    ai_model: str = "gpt-3.5-turbo"
    ai_api_key: Optional[str] = None
    ai_api_base: Optional[str] = None
    ai_max_tokens: int = 500
    ai_temperature: float = 0.8
    ai_timeout: int = 30
    
    # System Settings
    max_recent_actions: int = 20
    max_conversation_history: int = 10
    
    # NPC Settings
    default_npc_interest_threshold: float = 0.1
    max_relevant_actions: int = 10
    max_relevant_news: int = 5
    
    # Data Collection (for future modules)
    journal_watch_path: Optional[str] = None
    eddn_api_base: str = "https://eddn.edcd.io"
    galnet_api_base: str = "https://cms.zaonce.net"
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "elited_ai.log"
    
    @classmethod
    def from_env(cls) -> 'SystemConfig':
        """Create configuration from environment variables."""
        config = cls()
        
        # AI Configuration
        if os.getenv('OPENAI_API_KEY'):
            config.ai_provider = AIProvider.OPENAI
            config.ai_api_key = os.getenv('OPENAI_API_KEY')
            config.ai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        elif os.getenv('ANTHROPIC_API_KEY'):
            config.ai_provider = AIProvider.ANTHROPIC
            config.ai_api_key = os.getenv('ANTHROPIC_API_KEY')
            config.ai_model = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
        
        elif os.getenv('AZURE_OPENAI_API_KEY'):
            config.ai_provider = AIProvider.AZURE_OPENAI
            config.ai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
            config.ai_api_base = os.getenv('AZURE_OPENAI_ENDPOINT')
            config.ai_model = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-35-turbo')
        
        elif os.getenv('LOCAL_AI_BASE_URL'):
            config.ai_provider = AIProvider.LOCAL
            config.ai_api_base = os.getenv('LOCAL_AI_BASE_URL', 'http://localhost:11434')
            config.ai_model = os.getenv('LOCAL_AI_MODEL', 'llama2')
        
        # Other settings from env
        config.ai_max_tokens = int(os.getenv('AI_MAX_TOKENS', '500'))
        config.ai_temperature = float(os.getenv('AI_TEMPERATURE', '0.8'))
        config.journal_watch_path = os.getenv('ED_JOURNAL_PATH')
        config.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        return config
    
    def to_ai_config(self):
        """Convert to AIConfig object."""
        from .ai_service import AIConfig
        
        return AIConfig(
            provider=self.ai_provider,
            model=self.ai_model,
            api_key=self.ai_api_key,
            api_base=self.ai_api_base,
            max_tokens=self.ai_max_tokens,
            temperature=self.ai_temperature,
            timeout=self.ai_timeout
        )


# Default Elite Dangerous paths (Windows)
DEFAULT_ED_PATHS = {
    "journal": os.path.expanduser("~/Saved Games/Frontier Developments/Elite Dangerous"),
    "screenshots": os.path.expanduser("~/Pictures/Frontier Developments/Elite Dangerous"),
    "bindings": os.path.expanduser("~/AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings")
}

# Common NPC personality presets
NPC_PRESETS = {
    "friendly_trader": {
        "personality_traits": {"helpful": 0.8, "greedy": 0.4, "cautious": 0.7},
        "faction_attitudes": {"Federation": 0.3, "Empire": 0.3, "Alliance": 0.3}
    },
    "paranoid_pirate": {
        "personality_traits": {"aggressive": 0.9, "greedy": 0.9, "suspicious": 0.8},
        "faction_attitudes": {"Federation": -0.9, "Empire": -0.9, "Alliance": -0.8}
    },
    "curious_explorer": {
        "personality_traits": {"curious": 0.9, "independent": 0.8, "helpful": 0.6},
        "faction_attitudes": {"Federation": 0.1, "Empire": 0.1, "Alliance": 0.4}
    },
    "federal_officer": {
        "personality_traits": {"dutiful": 0.9, "authoritative": 0.7, "helpful": 0.6},
        "faction_attitudes": {"Federation": 0.9, "Empire": -0.6, "Alliance": -0.2}
    },
    "imperial_noble": {
        "personality_traits": {"arrogant": 0.7, "sophisticated": 0.8, "greedy": 0.5},
        "faction_attitudes": {"Federation": -0.7, "Empire": 0.9, "Alliance": -0.3}
    }
}

# AI Model recommendations
AI_MODEL_RECOMMENDATIONS = {
    "creative_roleplay": {
        "openai": "gpt-4",
        "anthropic": "claude-3-opus-20240229",
        "temperature": 0.9,
        "max_tokens": 600
    },
    "consistent_character": {
        "openai": "gpt-3.5-turbo",
        "anthropic": "claude-3-sonnet-20240229", 
        "temperature": 0.7,
        "max_tokens": 400
    },
    "budget_friendly": {
        "openai": "gpt-3.5-turbo",
        "anthropic": "claude-3-haiku-20240307",
        "temperature": 0.8,
        "max_tokens": 300
    }
}