"""
Data models for Elite Dangerous AI chatbot system.
Defines the structure of player data, world state, and NPC information.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class EventType(Enum):
    """Types of events the player can perform."""
    JUMP = "jump"
    TRADE = "trade"
    COMBAT = "combat"
    EXPLORATION = "exploration"
    MISSION = "mission"
    REPUTATION_GAIN = "reputation_gain"
    REPUTATION_LOSS = "reputation_loss"


class NPCType(Enum):
    """Types of NPCs with different personalities and interests."""
    TRADER = "trader"
    EXPLORER = "explorer"
    PIRATE = "pirate"
    BOUNTY_HUNTER = "bounty_hunter"
    FEDERAL_NAVY = "federal_navy"
    IMPERIAL_NAVY = "imperial_navy"
    ALLIANCE = "alliance"
    ENGINEER = "engineer"
    CITIZEN = "citizen"


@dataclass
class PlayerAction:
    """Represents a single player action or event."""
    event_type: EventType
    description: str
    timestamp: str
    location: Optional[str] = None
    target: Optional[str] = None  # Target faction, ship type, etc.
    value: Optional[float] = None  # Credit value, jump distance, etc.
    reputation_change: Dict[str, float] = field(default_factory=dict)


@dataclass
class PlayerStatus:
    """Current player status and statistics."""
    name: str
    current_system: str
    current_station: Optional[str] = None
    credits: float = 0.0
    ship_type: str = "Sidewinder"
    combat_rank: str = "Harmless"
    trade_rank: str = "Penniless"
    exploration_rank: str = "Aimless"
    
    # Reputation with major factions (-100 to 100)
    federation_rep: float = 0.0
    empire_rep: float = 0.0
    alliance_rep: float = 0.0
    
    # Recent actions (last 10-20 actions)
    recent_actions: List[PlayerAction] = field(default_factory=list)


@dataclass
class SystemState:
    """Information about the current star system."""
    name: str
    allegiance: Optional[str] = None
    government: Optional[str] = None
    economy: Optional[str] = None
    security_level: str = "Medium"
    population: int = 0
    controlling_faction: Optional[str] = None
    
    # Current events in the system
    active_conflicts: List[str] = field(default_factory=list)
    community_goals: List[str] = field(default_factory=list)


@dataclass
class GalacticNews:
    """Galaxy-wide news and events."""
    galnet_headlines: List[str] = field(default_factory=list)
    community_goals: List[str] = field(default_factory=list)
    powerplay_updates: List[str] = field(default_factory=list)
    thargoid_activity: List[str] = field(default_factory=list)


@dataclass
class NPCPersonality:
    """Defines an NPC's personality, background, and interests."""
    name: str
    npc_type: NPCType
    background_story: str
    
    # What types of events this NPC cares about (0.0 to 1.0)
    interest_weights: Dict[EventType, float] = field(default_factory=dict)
    
    # How this NPC views different factions (-1.0 to 1.0)
    faction_attitudes: Dict[str, float] = field(default_factory=dict)
    
    # Personality traits that affect conversation style
    personality_traits: Dict[str, float] = field(default_factory=dict)
    # Examples: "aggressive": 0.8, "helpful": 0.3, "greedy": 0.9
    
    # Current mood modifiers
    current_mood: Dict[str, float] = field(default_factory=dict)


@dataclass
class FilteredData:
    """Data that has been filtered and scored for a specific NPC."""
    npc: NPCPersonality
    relevant_player_actions: List[tuple[PlayerAction, float]] = field(default_factory=list)  # (action, sentiment_score)
    relevant_news: List[tuple[str, float]] = field(default_factory=list)  # (news_item, sentiment_score)
    relevant_system_info: Dict[str, float] = field(default_factory=dict)  # system_attribute -> sentiment_score
    player_reputation_view: float = 0.0  # Overall view of player (-1.0 to 1.0)


@dataclass
class ConversationContext:
    """Complete context for an AI conversation with an NPC."""
    npc: NPCPersonality
    player_status: PlayerStatus
    system_state: SystemState
    galactic_news: GalacticNews
    filtered_data: FilteredData
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy JSON serialization."""
        return {
            "npc_name": self.npc.name,
            "npc_type": self.npc.npc_type.value,
            "npc_background": self.npc.background_story,
            "player": {
                "name": self.player_status.name,
                "location": f"{self.player_status.current_system}/{self.player_status.current_station or 'In Space'}",
                "ship": self.player_status.ship_type,
                "credits": self.player_status.credits,
                "ranks": {
                    "combat": self.player_status.combat_rank,
                    "trade": self.player_status.trade_rank,
                    "exploration": self.player_status.exploration_rank
                },
                "reputation": {
                    "federation": self.player_status.federation_rep,
                    "empire": self.player_status.empire_rep,
                    "alliance": self.player_status.alliance_rep
                }
            },
            "system": {
                "name": self.system_state.name,
                "allegiance": self.system_state.allegiance,
                "security": self.system_state.security_level,
                "conflicts": self.system_state.active_conflicts
            },
            "filtered_data": {
                "relevant_actions": [
                    {"action": action.description, "sentiment": score}
                    for action, score in self.filtered_data.relevant_player_actions
                ],
                "relevant_news": [
                    {"news": news, "sentiment": score}
                    for news, score in self.filtered_data.relevant_news
                ],
                "reputation_view": self.filtered_data.player_reputation_view
            }
        }