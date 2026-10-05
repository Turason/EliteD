"""
NPC Filter System - Determines what data matters to each NPC and their sentiment about it.
This is the core intelligence that makes NPCs react differently to the same events.
"""

from typing import Dict, List, Tuple
from .models import (
    NPCPersonality, NPCType, EventType, PlayerAction, PlayerStatus, 
    SystemState, GalacticNews, FilteredData
)


class NPCFilter:
    """Filters and scores game data based on NPC personality and interests."""
    
    def __init__(self):
        """Initialize with default NPC templates."""
        self.npc_templates = self._create_default_templates()
    
    def filter_data_for_npc(
        self, 
        npc: NPCPersonality, 
        player_status: PlayerStatus, 
        system_state: SystemState,
        galactic_news: GalacticNews
    ) -> FilteredData:
        """Filter all game data through the lens of a specific NPC."""
        
        filtered_data = FilteredData(npc=npc)
        
        # Filter player actions and score sentiment
        filtered_data.relevant_player_actions = self._filter_player_actions(
            npc, player_status.recent_actions
        )
        
        # Filter news items
        filtered_data.relevant_news = self._filter_news(npc, galactic_news)
        
        # Evaluate system information
        filtered_data.relevant_system_info = self._evaluate_system(npc, system_state)
        
        # Calculate overall view of player
        filtered_data.player_reputation_view = self._calculate_player_reputation_view(
            npc, player_status, filtered_data.relevant_player_actions
        )
        
        return filtered_data
    
    def _filter_player_actions(
        self, npc: NPCPersonality, actions: List[PlayerAction]
    ) -> List[Tuple[PlayerAction, float]]:
        """Filter player actions and assign sentiment scores."""
        relevant_actions = []
        
        for action in actions:
            # Check if NPC cares about this type of action
            interest_level = npc.interest_weights.get(action.event_type, 0.0)
            
            if interest_level > 0.1:  # Only include if NPC has some interest
                sentiment = self._calculate_action_sentiment(npc, action)
                relevant_actions.append((action, sentiment * interest_level))
        
        # Sort by relevance (absolute sentiment * interest)
        relevant_actions.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # Return top 10 most relevant actions
        return relevant_actions[:10]
    
    def _calculate_action_sentiment(self, npc: NPCPersonality, action: PlayerAction) -> float:
        """Calculate how an NPC feels about a specific player action (-1.0 to 1.0)."""
        sentiment = 0.0
        
        # Base sentiment based on action type and NPC personality
        if action.event_type == EventType.TRADE:
            if npc.npc_type == NPCType.TRADER:
                sentiment += 0.8  # Traders love trade
            elif npc.npc_type == NPCType.PIRATE:
                sentiment += 0.3  # Pirates see traders as targets
        
        elif action.event_type == EventType.COMBAT:
            if npc.npc_type == NPCType.PIRATE:
                sentiment += 0.6  # Pirates like combat
            elif npc.npc_type == NPCType.BOUNTY_HUNTER:
                sentiment += 0.9  # Bounty hunters love combat
            elif npc.npc_type == NPCType.TRADER:
                sentiment -= 0.4  # Traders are cautious about violent players
        
        elif action.event_type == EventType.EXPLORATION:
            if npc.npc_type == NPCType.EXPLORER:
                sentiment += 0.9  # Explorers love exploration
            elif npc.npc_type == NPCType.ENGINEER:
                sentiment += 0.5  # Engineers appreciate data
        
        # Faction-based sentiment
        if action.target and action.target in npc.faction_attitudes:
            faction_sentiment = npc.faction_attitudes[action.target]
            if action.event_type == EventType.REPUTATION_GAIN:
                sentiment += faction_sentiment
            elif action.event_type == EventType.REPUTATION_LOSS:
                sentiment -= faction_sentiment
        
        # Personality trait modifiers
        if "aggressive" in npc.personality_traits:
            if action.event_type == EventType.COMBAT:
                sentiment += npc.personality_traits["aggressive"] * 0.5
        
        if "greedy" in npc.personality_traits:
            if action.value and action.value > 1000000:  # Big money deals
                sentiment += npc.personality_traits["greedy"] * 0.3
        
        # Clamp sentiment to valid range
        return max(-1.0, min(1.0, sentiment))
    
    def _filter_news(self, npc: NPCPersonality, news: GalacticNews) -> List[Tuple[str, float]]:
        """Evaluate all galactic news for this NPC and assign sentiment scores."""
        all_news = []
        
        # Check each news category - all NPCs know all news
        for headline in news.galnet_headlines:
            sentiment = self._evaluate_news_sentiment(npc, headline, "galnet")
            all_news.append((f"GalNet: {headline}", sentiment))
        
        for goal in news.community_goals:
            sentiment = self._evaluate_news_sentiment(npc, goal, "community_goal")
            all_news.append((f"Community Goal: {goal}", sentiment))
        
        for update in news.thargoid_activity:
            sentiment = self._evaluate_news_sentiment(npc, update, "thargoid")
            all_news.append((f"Thargoid Activity: {update}", sentiment))
        
        # Sort by strength of opinion (strongest first), keeping all news items
        all_news.sort(key=lambda x: abs(x[1]), reverse=True)
        return all_news
    
    def _evaluate_news_sentiment(self, npc: NPCPersonality, item: str, category: str) -> float:
        """Evaluate how an NPC feels about a news item."""
        sentiment = 0.0
        item_lower = item.lower()
        
        # Category-based base sentiment
        if category == "thargoid":
            if npc.npc_type in [NPCType.FEDERAL_NAVY, NPCType.IMPERIAL_NAVY, NPCType.ALLIANCE]:
                sentiment -= 0.8  # Military NPCs concerned about Thargoids
            elif npc.npc_type == NPCType.TRADER:
                sentiment -= 0.6  # Trade disruption
            elif npc.npc_type == NPCType.PIRATE:
                sentiment -= 0.5  # Dangerous alien threat
            elif npc.npc_type == NPCType.EXPLORER:
                sentiment += 0.3  # Scientific curiosity
            else:
                sentiment -= 0.4
        
        # Faction sentiment from news mentions
        for faction, attitude in npc.faction_attitudes.items():
            if faction.lower() in item_lower:
                sentiment += attitude * 0.5
        
        # Keyword-based sentiment
        if "trade" in item_lower or "market" in item_lower:
            if npc.npc_type == NPCType.TRADER:
                sentiment += 0.5
            elif npc.npc_type == NPCType.PIRATE:
                sentiment += 0.3  # Trade routes mean cargo targets
        
        if "navy" in item_lower or "patrol" in item_lower or "security" in item_lower:
            if npc.npc_type == NPCType.PIRATE:
                sentiment -= 0.6  # Law enforcement tightens
            elif npc.npc_type in [NPCType.FEDERAL_NAVY, NPCType.IMPERIAL_NAVY, NPCType.BOUNTY_HUNTER]:
                sentiment += 0.5
            elif npc.npc_type == NPCType.TRADER:
                sentiment += 0.4  # Safety
        
        if "pirate" in item_lower or "outlaw" in item_lower:
            if npc.npc_type == NPCType.PIRATE:
                sentiment += 0.5
            elif npc.npc_type in [NPCType.BOUNTY_HUNTER, NPCType.TRADER, NPCType.FEDERAL_NAVY]:
                sentiment -= 0.6
        
        if "war" in item_lower or "conflict" in item_lower:
            if npc.npc_type in [NPCType.BOUNTY_HUNTER, NPCType.PIRATE]:
                sentiment += 0.4  # Conflict creates opportunities
            elif npc.npc_type == NPCType.TRADER:
                sentiment -= 0.5  # War disrupts trade
        
        if "discovery" in item_lower or "exploration" in item_lower or "terraforming" in item_lower:
            if npc.npc_type == NPCType.EXPLORER:
                sentiment += 0.8
            elif npc.npc_type == NPCType.ENGINEER:
                sentiment += 0.6
            elif npc.npc_type == NPCType.TRADER:
                sentiment += 0.3  # New markets
        
        return max(-1.0, min(1.0, sentiment))
    
    def _evaluate_system(self, npc: NPCPersonality, system: SystemState) -> Dict[str, float]:
        """Evaluate how an NPC feels about various system attributes."""
        system_sentiment = {}
        
        # Security level sentiment
        if system.security_level == "High":
            if npc.npc_type in [NPCType.TRADER, NPCType.CITIZEN]:
                system_sentiment["security"] = 0.8  # Safe for honest folk
            elif npc.npc_type == NPCType.PIRATE:
                system_sentiment["security"] = -0.9  # Bad for pirates
        
        elif system.security_level == "Low" or system.security_level == "Anarchy":
            if npc.npc_type == NPCType.PIRATE:
                system_sentiment["security"] = 0.9  # Great for pirates
            elif npc.npc_type == NPCType.BOUNTY_HUNTER:
                system_sentiment["security"] = 0.7  # More targets
            else:
                system_sentiment["security"] = -0.6  # Dangerous for others
        
        # Allegiance sentiment
        if system.allegiance and system.allegiance in npc.faction_attitudes:
            system_sentiment["allegiance"] = npc.faction_attitudes[system.allegiance]
        
        # Conflict sentiment
        if system.active_conflicts:
            if npc.npc_type in [NPCType.BOUNTY_HUNTER, NPCType.PIRATE]:
                system_sentiment["conflicts"] = 0.6  # Opportunity
            else:
                system_sentiment["conflicts"] = -0.4  # Instability
        
        return system_sentiment
    
    def _calculate_player_reputation_view(
        self, 
        npc: NPCPersonality, 
        player_status: PlayerStatus,
        relevant_actions: List[Tuple[PlayerAction, float]]
    ) -> float:
        """Calculate overall NPC opinion of the player."""
        total_sentiment = 0.0
        action_count = 0
        
        # Factor in recent actions
        for action, sentiment in relevant_actions:
            total_sentiment += sentiment
            action_count += 1
        
        # Factor in faction reputation
        faction_bonus = 0.0
        if "Federation" in npc.faction_attitudes:
            faction_bonus += npc.faction_attitudes["Federation"] * (player_status.federation_rep / 100.0)
        if "Empire" in npc.faction_attitudes:
            faction_bonus += npc.faction_attitudes["Empire"] * (player_status.empire_rep / 100.0)
        if "Alliance" in npc.faction_attitudes:
            faction_bonus += npc.faction_attitudes["Alliance"] * (player_status.alliance_rep / 100.0)
        
        # Calculate weighted average
        if action_count > 0:
            action_sentiment = total_sentiment / action_count
            # Weight: 70% actions, 30% faction reputation
            final_sentiment = (action_sentiment * 0.7) + (faction_bonus * 0.3)
        else:
            final_sentiment = faction_bonus
        
        return max(-1.0, min(1.0, final_sentiment))
    
    def _create_default_templates(self) -> Dict[NPCType, NPCPersonality]:
        """Create default personality templates for different NPC types."""
        templates = {}
        
        # Trader Template
        templates[NPCType.TRADER] = NPCPersonality(
            name="Default Trader",
            npc_type=NPCType.TRADER,
            background_story="A merchant focused on profit and safe trade routes.",
            interest_weights={
                EventType.TRADE: 1.0,
                EventType.EXPLORATION: 0.3,
                EventType.COMBAT: 0.2,
                EventType.REPUTATION_GAIN: 0.5,
                EventType.REPUTATION_LOSS: 0.5
            },
            faction_attitudes={
                "Federation": 0.2,
                "Empire": 0.2,
                "Alliance": 0.2
            },
            personality_traits={
                "greedy": 0.8,
                "cautious": 0.9,
                "helpful": 0.6
            }
        )
        
        # Pirate Template
        templates[NPCType.PIRATE] = NPCPersonality(
            name="Default Pirate",
            npc_type=NPCType.PIRATE,
            background_story="A dangerous outlaw who preys on merchants and cargo ships.",
            interest_weights={
                EventType.COMBAT: 1.0,
                EventType.TRADE: 0.7,  # Interested in cargo targets
                EventType.REPUTATION_LOSS: 0.8,  # Likes troublemakers
                EventType.REPUTATION_GAIN: 0.3
            },
            faction_attitudes={
                "Federation": -0.8,
                "Empire": -0.8,
                "Alliance": -0.6
            },
            personality_traits={
                "aggressive": 0.9,
                "greedy": 0.9,
                "helpful": 0.1
            }
        )
        
        # Explorer Template
        templates[NPCType.EXPLORER] = NPCPersonality(
            name="Default Explorer",
            npc_type=NPCType.EXPLORER,
            background_story="A seasoned explorer seeking the unknown reaches of the galaxy.",
            interest_weights={
                EventType.EXPLORATION: 1.0,
                EventType.JUMP: 0.8,
                EventType.TRADE: 0.2,
                EventType.COMBAT: 0.1
            },
            faction_attitudes={
                "Federation": 0.1,
                "Empire": 0.1,
                "Alliance": 0.3  # Slightly Alliance-friendly
            },
            personality_traits={
                "curious": 0.9,
                "independent": 0.8,
                "helpful": 0.7
            }
        )

        templates[NPCType.BOUNTY_HUNTER] = NPCPersonality(
            name="Default Bounty Hunter",
            npc_type=NPCType.BOUNTY_HUNTER,
            background_story="A licensed hunter who tracks wanted criminals and takes dangerous contracts for the reward.",
            interest_weights={
                EventType.COMBAT: 1.0,
                EventType.MISSION: 0.8,
                EventType.JUMP: 0.4,
                EventType.REPUTATION_GAIN: 0.6,
                EventType.REPUTATION_LOSS: 0.5,
            },
            faction_attitudes={"Federation": 0.5, "Empire": 0.3, "Alliance": 0.3, "Pirates": -0.9},
            personality_traits={"persistent": 0.9, "observant": 0.8, "helpful": 0.6},
        )

        templates[NPCType.FEDERAL_NAVY] = NPCPersonality(
            name="Default Federal Navy Officer",
            npc_type=NPCType.FEDERAL_NAVY,
            background_story="A Federal officer balancing patrol duties, faction security, and the needs of the people under their protection.",
            interest_weights={
                EventType.COMBAT: 0.8,
                EventType.MISSION: 1.0,
                EventType.REPUTATION_GAIN: 0.9,
                EventType.REPUTATION_LOSS: 0.8,
                EventType.JUMP: 0.4,
            },
            faction_attitudes={"Federation": 0.9, "Empire": -0.6, "Alliance": 0.1, "Pirates": -0.8},
            personality_traits={"disciplined": 0.9, "patriotic": 0.8, "helpful": 0.5},
        )

        templates[NPCType.IMPERIAL_NAVY] = NPCPersonality(
            name="Default Imperial Navy Officer",
            npc_type=NPCType.IMPERIAL_NAVY,
            background_story="An Imperial officer devoted to the Empire, its hierarchy, and the security of its systems.",
            interest_weights={
                EventType.COMBAT: 0.8,
                EventType.MISSION: 1.0,
                EventType.REPUTATION_GAIN: 0.9,
                EventType.REPUTATION_LOSS: 0.8,
                EventType.JUMP: 0.4,
            },
            faction_attitudes={"Federation": -0.6, "Empire": 0.9, "Alliance": -0.2, "Pirates": -0.8},
            personality_traits={"disciplined": 0.8, "proud": 0.9, "helpful": 0.4},
        )

        templates[NPCType.ALLIANCE] = NPCPersonality(
            name="Default Alliance Liaison",
            npc_type=NPCType.ALLIANCE,
            background_story="An Alliance representative coordinating local aid, diplomacy, and the defense of member systems.",
            interest_weights={
                EventType.MISSION: 0.9,
                EventType.TRADE: 0.7,
                EventType.COMBAT: 0.6,
                EventType.REPUTATION_GAIN: 0.8,
                EventType.REPUTATION_LOSS: 0.7,
                EventType.EXPLORATION: 0.4,
            },
            faction_attitudes={"Federation": 0.1, "Empire": -0.2, "Alliance": 0.9, "Pirates": -0.7},
            personality_traits={"diplomatic": 0.9, "pragmatic": 0.8, "helpful": 0.7},
        )

        templates[NPCType.ENGINEER] = NPCPersonality(
            name="Default Engineer",
            npc_type=NPCType.ENGINEER,
            background_story="A technically minded engineer seeking rare materials, useful research data, and capable pilots for workshop jobs.",
            interest_weights={
                EventType.EXPLORATION: 0.8,
                EventType.MISSION: 0.8,
                EventType.TRADE: 0.6,
                EventType.COMBAT: 0.3,
                EventType.JUMP: 0.5,
            },
            faction_attitudes={"Federation": 0.1, "Empire": 0.1, "Alliance": 0.1},
            personality_traits={"curious": 0.9, "practical": 0.8, "helpful": 0.6},
        )

        templates[NPCType.CITIZEN] = NPCPersonality(
            name="Default Citizen",
            npc_type=NPCType.CITIZEN,
            background_story="A station resident concerned with local safety, reliable supplies, and the fortunes of ordinary people.",
            interest_weights={
                EventType.MISSION: 0.8,
                EventType.TRADE: 0.6,
                EventType.COMBAT: 0.4,
                EventType.REPUTATION_GAIN: 0.5,
                EventType.REPUTATION_LOSS: 0.5,
                EventType.JUMP: 0.2,
            },
            faction_attitudes={"Federation": 0.1, "Empire": 0.0, "Alliance": 0.2, "Pirates": -0.6},
            personality_traits={"cautious": 0.7, "community-minded": 0.9, "helpful": 0.8},
        )
        
        return templates
    
    def get_template(self, npc_type: NPCType) -> NPCPersonality:
        """Get a default personality template for an NPC type."""
        return self.npc_templates.get(npc_type, self.npc_templates[NPCType.TRADER])
    
    def create_custom_npc(
        self, 
        name: str, 
        npc_type: NPCType, 
        background: str,
        custom_interests: Dict[EventType, float] = None,
        custom_attitudes: Dict[str, float] = None,
        custom_traits: Dict[str, float] = None
    ) -> NPCPersonality:
        """Create a custom NPC based on a template with overrides."""
        template = self.get_template(npc_type)
        
        return NPCPersonality(
            name=name,
            npc_type=npc_type,
            background_story=background,
            interest_weights=custom_interests or template.interest_weights.copy(),
            faction_attitudes=custom_attitudes or template.faction_attitudes.copy(),
            personality_traits=custom_traits or template.personality_traits.copy()
        )