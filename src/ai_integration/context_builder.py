"""
Context Builder - Assembles filtered data into conversation context for AI.
Creates rich, structured prompts that give the AI all the information needed
to roleplay as a specific NPC with appropriate reactions to game events.
"""

from typing import Dict, List, Optional
import json
from .models import (
    ConversationContext, NPCPersonality, PlayerStatus, SystemState, 
    GalacticNews, FilteredData, EventType
)


class ContextBuilder:
    """Builds conversation context for AI from filtered game data."""
    
    def __init__(self):
        """Initialize context builder with prompt templates."""
        self.base_system_prompt = self._create_base_system_prompt()
    
    def build_context(
        self,
        npc: NPCPersonality,
        player_status: PlayerStatus,
        system_state: SystemState,
        galactic_news: GalacticNews,
        filtered_data: FilteredData,
        conversation_history: List[Dict[str, str]] = None
    ) -> ConversationContext:
        """Build complete conversation context for AI."""
        
        context = ConversationContext(
            npc=npc,
            player_status=player_status,
            system_state=system_state,
            galactic_news=galactic_news,
            filtered_data=filtered_data,
            conversation_history=conversation_history or []
        )
        
        return context
    
    def create_ai_prompt(self, context: ConversationContext) -> Dict[str, str]:
        """Create structured prompt for AI conversation."""
        
        system_prompt = self._build_system_prompt(context)
        user_prompt = self._build_user_prompt(context)
        
        return {
            "system": system_prompt,
            "user": user_prompt,
            "context_data": json.dumps(context.to_dict(), indent=2)
        }
    
    def _build_system_prompt(self, context: ConversationContext) -> str:
        """Build the system prompt that defines the NPC's role and personality."""
        
        npc = context.npc
        system_info = context.system_state
        
        # Base personality description
        personality_desc = self._describe_personality(npc)
        
        # Current location and situation
        location_desc = f"You are currently in the {system_info.name} system"
        if system_info.controlling_faction:
            location_desc += f", controlled by {system_info.controlling_faction}"
        if system_info.allegiance:
            location_desc += f" (aligned with the {system_info.allegiance})"
        location_desc += f". Security level is {system_info.security_level}."
        
        # Conflicts and current events
        situation_desc = ""
        if system_info.active_conflicts:
            situation_desc += f" Active conflicts: {', '.join(system_info.active_conflicts)}."
        if system_info.community_goals:
            situation_desc += f" Community goals active: {', '.join(system_info.community_goals)}."
        
        # NPC's current opinion of the player
        opinion_desc = self._describe_player_opinion(context.filtered_data)
        
        system_prompt = f"""{self.base_system_prompt}

CHARACTER DETAILS:
Name: {npc.name}
Type: {npc.npc_type.value.replace('_', ' ').title()}
Background: {npc.background_story}

PERSONALITY:
{personality_desc}

CURRENT SITUATION:
{location_desc}{situation_desc}

YOUR VIEW OF THE PLAYER:
{opinion_desc}

CONVERSATION GUIDELINES:
- Stay completely in character as {npc.name}
- React authentically based on your personality and the player's reputation with you
- Reference relevant recent events, news, or player actions when appropriate
- Your responses should reflect your background as a {npc.npc_type.value.replace('_', ' ')}
- Show appropriate emotional reactions to topics you care about
- Keep responses conversational and immersive (2-4 sentences typically)
- Use Elite Dangerous terminology and lore naturally"""

        return system_prompt
    
    def _build_user_prompt(self, context: ConversationContext) -> str:
        """Build the user prompt with current game state and recent events."""
        
        player = context.player_status
        filtered = context.filtered_data
        
        prompt_parts = []
        
        # Player introduction
        player_intro = f"""PLAYER INFORMATION:
Commander {player.name} approaches you in their {player.ship_type}.
- Credits: {player.credits:,.0f}
- Combat Rank: {player.combat_rank}
- Trade Rank: {player.trade_rank}  
- Exploration Rank: {player.exploration_rank}
- Federation Reputation: {player.federation_rep:.1f}/100
- Empire Reputation: {player.empire_rep:.1f}/100
- Alliance Reputation: {player.alliance_rep:.1f}/100"""
        
        prompt_parts.append(player_intro)
        
        # Recent relevant player actions
        if filtered.relevant_player_actions:
            actions_text = "RECENT PLAYER ACTIONS (that you care about):"
            for action, sentiment in filtered.relevant_player_actions[:5]:  # Top 5 most relevant
                sentiment_word = self._sentiment_to_word(sentiment)
                actions_text += f"\n- {action.description} [{sentiment_word}]"
                if action.location:
                    actions_text += f" (in {action.location})"
                if action.value:
                    actions_text += f" - {action.value:,.0f} CR"
            
            prompt_parts.append(actions_text)
        
        # Relevant galactic news
        if filtered.relevant_news:
            news_text = "RECENT NEWS (that interests you):"
            for news, sentiment in filtered.relevant_news[:3]:  # Top 3 most relevant
                sentiment_word = self._sentiment_to_word(sentiment)
                news_text += f"\n- {news} [{sentiment_word}]"
            
            prompt_parts.append(news_text)
        
        # System situation relevance
        if filtered.relevant_system_info:
            system_text = "CURRENT SYSTEM SITUATION (your view):"
            for aspect, sentiment in filtered.relevant_system_info.items():
                sentiment_word = self._sentiment_to_word(sentiment)
                system_text += f"\n- {aspect.title()}: {sentiment_word}"
            
            prompt_parts.append(system_text)
        
        # Conversation starter
        starter = f"\nCommander {player.name} wants to talk to you. Greet them and start a conversation based on your personality and your current opinion of them."
        prompt_parts.append(starter)
        
        return "\n\n".join(prompt_parts)
    
    def _describe_personality(self, npc: NPCPersonality) -> str:
        """Create a natural description of the NPC's personality."""
        traits = []
        
        for trait, value in npc.personality_traits.items():
            if value > 0.7:
                traits.append(f"very {trait}")
            elif value > 0.5:
                traits.append(f"quite {trait}")
            elif value > 0.3:
                traits.append(f"somewhat {trait}")
        
        interests = []
        for event_type, weight in npc.interest_weights.items():
            if weight > 0.7:
                interests.append(event_type.value.replace('_', ' '))
        
        description = f"You are {', '.join(traits[:3])}." if traits else "You have a balanced personality."
        
        if interests:
            description += f" You are particularly interested in {', '.join(interests)}."
        
        # Faction attitudes
        strong_likes = []
        strong_dislikes = []
        for faction, attitude in npc.faction_attitudes.items():
            if attitude > 0.5:
                strong_likes.append(faction)
            elif attitude < -0.5:
                strong_dislikes.append(faction)
        
        if strong_likes:
            description += f" You strongly support the {', '.join(strong_likes)}."
        if strong_dislikes:
            description += f" You have negative feelings toward the {', '.join(strong_dislikes)}."
        
        return description
    
    def _describe_player_opinion(self, filtered_data: FilteredData) -> str:
        """Describe the NPC's current opinion of the player."""
        reputation = filtered_data.player_reputation_view
        
        if reputation > 0.7:
            return "You have a very positive opinion of this Commander. They seem trustworthy and skilled."
        elif reputation > 0.3:
            return "You have a generally favorable impression of this Commander."
        elif reputation > -0.3:
            return "You are neutral toward this Commander. You don't know much about them yet."
        elif reputation > -0.7:
            return "You have some concerns about this Commander. Their recent actions have been questionable."
        else:
            return "You view this Commander with suspicion or hostility. They have a poor reputation with you."
    
    def _sentiment_to_word(self, sentiment: float) -> str:
        """Convert sentiment score to descriptive word."""
        if sentiment > 0.7:
            return "VERY POSITIVE"
        elif sentiment > 0.3:
            return "positive"
        elif sentiment > -0.3:
            return "neutral"
        elif sentiment > -0.7:
            return "negative"
        else:
            return "VERY NEGATIVE"
    
    def _create_base_system_prompt(self) -> str:
        """Create the base system prompt for Elite Dangerous NPCs."""
        return """You are roleplaying as an NPC character in the Elite Dangerous universe. This is a space simulation game set in the year 3310, where humanity has spread across the galaxy.

UNIVERSE CONTEXT:
- The galaxy is populated by three major powers: the Federation, Empire, and Alliance
- Independent systems and factions also exist throughout human space
- Players (Commanders) pilot ships for trading, exploring, bounty hunting, piracy, etc.
- The galaxy faces threats like the Thargoids (alien species)
- Political intrigue, wars, and economic competition drive galactic events

YOUR ROLE:
You are a living person in this universe with your own goals, opinions, and reactions. You should respond naturally to the player based on:
- Your personal background and profession
- Your opinion of their recent actions and reputation  
- Current events that affect you or your interests
- Your personality traits and faction loyalties

IMPORTANT: You are NOT an AI assistant. You are a character living in the Elite Dangerous universe. Never break character or reference being an AI."""