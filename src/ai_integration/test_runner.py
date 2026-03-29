"""
Test Runner - Test the AI integration system with constructed data.
This allows you to test NPCs, prompts, and AI responses without needing real game data.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

from .models import (
    PlayerAction, PlayerStatus, SystemState, GalacticNews, NPCPersonality,
    EventType, NPCType, ConversationContext
)
from .npc_filter import NPCFilter
from .context_builder import ContextBuilder
from .ai_service import AIService, AIConfig, AIProvider, create_openai_config, create_anthropic_config, create_local_config


class TestRunner:
    """Test the AI NPC system with constructed data."""
    
    def __init__(self, ai_config: Optional[AIConfig] = None):
        """Initialize test runner."""
        self.npc_filter = NPCFilter()
        self.context_builder = ContextBuilder()
        self.ai_service = AIService(ai_config) if ai_config else None
        
        # Sample data for testing
        self.sample_data = self._create_sample_data()
    
    def test_npc_filtering(self, npc_name: str = "Test Trader") -> Dict:
        """Test the NPC filtering system with sample data."""
        print(f"\n=== Testing NPC Filtering for {npc_name} ===")
        
        # Get or create NPC
        npc = self._get_test_npc(npc_name)
        
        # Filter data through NPC perspective
        filtered_data = self.npc_filter.filter_data_for_npc(
            npc,
            self.sample_data["player_status"],
            self.sample_data["system_state"],
            self.sample_data["galactic_news"]
        )
        
        # Print results
        result = {
            "npc_name": npc.name,
            "npc_type": npc.npc_type.value,
            "player_reputation_view": filtered_data.player_reputation_view,
            "relevant_actions": [
                {
                    "action": action.description,
                    "sentiment": sentiment,
                    "location": action.location
                }
                for action, sentiment in filtered_data.relevant_player_actions
            ],
            "relevant_news": [
                {
                    "news": news,
                    "sentiment": sentiment
                }
                for news, sentiment in filtered_data.relevant_news
            ],
            "system_views": filtered_data.relevant_system_info
        }
        
        print(f"Overall Opinion of Player: {filtered_data.player_reputation_view:.2f}")
        print(f"Relevant Actions: {len(filtered_data.relevant_player_actions)}")
        print(f"Relevant News: {len(filtered_data.relevant_news)}")
        print(f"System Opinions: {len(filtered_data.relevant_system_info)}")
        
        return result
    
    def test_context_building(self, npc_name: str = "Test Trader") -> Dict[str, str]:
        """Test the context building system."""
        print(f"\n=== Testing Context Building for {npc_name} ===")
        
        # Get NPC and filter data
        npc = self._get_test_npc(npc_name)
        filtered_data = self.npc_filter.filter_data_for_npc(
            npc,
            self.sample_data["player_status"],
            self.sample_data["system_state"],
            self.sample_data["galactic_news"]
        )
        
        # Build context
        context = self.context_builder.build_context(
            npc,
            self.sample_data["player_status"],
            self.sample_data["system_state"],
            self.sample_data["galactic_news"],
            filtered_data
        )
        
        # Create AI prompts
        prompts = self.context_builder.create_ai_prompt(context)
        
        print("Generated Prompts:")
        print(f"- System Prompt Length: {len(prompts['system'])} characters")
        print(f"- User Prompt Length: {len(prompts['user'])} characters")
        print("\nSystem Prompt Preview:")
        print(prompts['system'][:500] + "..." if len(prompts['system']) > 500 else prompts['system'])
        
        return prompts
    
    async def test_ai_integration(
        self, 
        npc_name: str = "Test Trader",
        test_message: str = "Hello! How's business?"
    ) -> Optional[str]:
        """Test the complete AI integration with a sample conversation."""
        if not self.ai_service:
            print("\n=== AI Integration Test Skipped ===")
            print("No AI configuration provided. Set up AI service to test responses.")
            return None
        
        print(f"\n=== Testing AI Integration for {npc_name} ===")
        print(f"Test Message: '{test_message}'")
        
        try:
            # Get NPC and build context
            npc = self._get_test_npc(npc_name)
            filtered_data = self.npc_filter.filter_data_for_npc(
                npc,
                self.sample_data["player_status"],
                self.sample_data["system_state"],
                self.sample_data["galactic_news"]
            )
            
            context = self.context_builder.build_context(
                npc,
                self.sample_data["player_status"],
                self.sample_data["system_state"],
                self.sample_data["galactic_news"],
                filtered_data
            )
            
            # Create prompts
            prompts = self.context_builder.create_ai_prompt(context)
            
            # Add user message to prompt
            full_user_prompt = f"{prompts['user']}\n\nPlayer says: \"{test_message}\"\n\nRespond as {npc.name}:"
            
            # Get AI response
            print("Sending to AI...")
            response = await self.ai_service.generate_response(
                prompts['system'],
                full_user_prompt
            )
            
            if response.error:
                print(f"AI Error: {response.error}")
                return None
            
            print(f"\n--- AI Response ({response.model}) ---")
            print(response.content)
            print(f"\nResponse generated in {response.response_time:.2f} seconds")
            if response.tokens_used:
                print(f"Tokens used: {response.tokens_used}")
            if response.cost_estimate:
                print(f"Estimated cost: ${response.cost_estimate:.4f}")
            
            return response.content
            
        except Exception as e:
            print(f"Error during AI integration test: {e}")
            return None
    
    def run_full_test_suite(self, npc_name: str = "Test Trader", ai_message: str = "Hello!"):
        """Run the complete test suite."""
        print("=" * 60)
        print("ELITE DANGEROUS AI NPC SYSTEM - FULL TEST SUITE")
        print("=" * 60)
        
        # Test 1: NPC Filtering
        filter_result = self.test_npc_filtering(npc_name)
        
        # Test 2: Context Building
        prompt_result = self.test_context_building(npc_name)
        
        # Test 3: AI Integration (if configured)
        if self.ai_service:
            asyncio.run(self.test_ai_integration(npc_name, ai_message))
        else:
            print("\n=== AI Integration Test Skipped ===")
            print("Configure AI service with set_ai_config() to test AI responses.")
        
        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETE")
        print("=" * 60)
        
        return {
            "filtering": filter_result,
            "context": prompt_result
        }
    
    def set_ai_config(self, config: AIConfig):
        """Set AI configuration for testing."""
        self.ai_service = AIService(config)
        print(f"AI service configured: {config.provider.value} - {config.model}")
    
    def create_custom_npc_test(
        self,
        name: str,
        npc_type: NPCType,
        background: str,
        custom_interests: Dict[EventType, float] = None,
        custom_attitudes: Dict[str, float] = None,
        custom_traits: Dict[str, float] = None
    ) -> NPCPersonality:
        """Create a custom NPC for testing."""
        npc = self.npc_filter.create_custom_npc(
            name, npc_type, background, 
            custom_interests, custom_attitudes, custom_traits
        )
        
        print(f"Created custom NPC: {name} ({npc_type.value})")
        print(f"Background: {background}")
        
        return npc
    
    def modify_sample_data(
        self,
        player_actions: List[Dict] = None,
        system_info: Dict = None,
        news: List[str] = None
    ):
        """Modify sample data for testing different scenarios."""
        if player_actions:
            actions = []
            for action_data in player_actions:
                action = PlayerAction(
                    event_type=EventType(action_data["type"]),
                    description=action_data["description"],
                    timestamp=action_data.get("timestamp", "2024-03-29T12:00:00Z"),
                    location=action_data.get("location"),
                    target=action_data.get("target"),
                    value=action_data.get("value")
                )
                actions.append(action)
            self.sample_data["player_status"].recent_actions = actions
        
        if system_info:
            for key, value in system_info.items():
                setattr(self.sample_data["system_state"], key, value)
        
        if news:
            self.sample_data["galactic_news"].galnet_headlines = news
    
    def _get_test_npc(self, name: str) -> NPCPersonality:
        """Get a test NPC, creating one if it doesn't exist."""
        if name == "Test Trader":
            return self.npc_filter.get_template(NPCType.TRADER)
        elif name == "Test Pirate":
            return self.npc_filter.get_template(NPCType.PIRATE)
        elif name == "Test Explorer":
            return self.npc_filter.get_template(NPCType.EXPLORER)
        else:
            # Create a custom trader by default
            return self.npc_filter.create_custom_npc(
                name, NPCType.TRADER, "A generic trader for testing purposes."
            )
    
    def _create_sample_data(self) -> Dict:
        """Create sample game data for testing."""
        
        # Sample player actions
        sample_actions = [
            PlayerAction(
                event_type=EventType.TRADE,
                description="Sold 50 tons of gold at Jameson Memorial",
                timestamp="2024-03-29T10:30:00Z",
                location="Shinrarta Dezhra",
                value=2500000.0
            ),
            PlayerAction(
                event_type=EventType.COMBAT,
                description="Destroyed a wanted Anaconda",
                timestamp="2024-03-29T09:15:00Z",
                location="Wolf 359",
                target="Pirates",
                value=850000.0
            ),
            PlayerAction(
                event_type=EventType.EXPLORATION,
                description="Discovered new Earth-like world",
                timestamp="2024-03-28T18:45:00Z",
                location="Unexplored System",
                value=1200000.0
            ),
            PlayerAction(
                event_type=EventType.REPUTATION_GAIN,
                description="Completed Federal Navy mission",
                timestamp="2024-03-28T14:20:00Z",
                target="Federation",
                reputation_change={"Federation": 5.0}
            )
        ]
        
        # Sample player status
        player_status = PlayerStatus(
            name="Commander Test",
            current_system="Sol",
            current_station="Abraham Lincoln",
            credits=15750000.0,
            ship_type="Python",
            combat_rank="Expert",
            trade_rank="Entrepreneur", 
            exploration_rank="Pathfinder",
            federation_rep=65.0,
            empire_rep=-10.0,
            alliance_rep=25.0,
            recent_actions=sample_actions
        )
        
        # Sample system state
        system_state = SystemState(
            name="Sol",
            allegiance="Federation",
            government="Democracy",
            economy="High Tech",
            security_level="High",
            population=22780000000,
            controlling_faction="Federal Congress",
            active_conflicts=["Civil War in Wolf 359"],
            community_goals=["Federal Navy Recruitment Drive"]
        )
        
        # Sample galactic news
        galactic_news = GalacticNews(
            galnet_headlines=[
                "Federal Navy Reports Increased Thargoid Activity",
                "New Trade Route Opens Between Sol and Shinrarta Dezhra", 
                "Imperial Wedding Celebrations Begin",
                "Alliance Explores New Terraforming Technology"
            ],
            community_goals=[
                "Federal Navy Recruitment Drive",
                "Trade Goods Needed for Colonia Expansion"
            ],
            thargoid_activity=[
                "Thargoid scouts spotted in Pleiades sector"
            ]
        )
        
        return {
            "player_status": player_status,
            "system_state": system_state,
            "galactic_news": galactic_news
        }


# Example usage functions
def demo_basic_test():
    """Demonstrate basic testing without AI."""
    print("Running basic test (no AI required)...")
    
    runner = TestRunner()
    
    # Test different NPC types
    for npc_type in ["Test Trader", "Test Pirate", "Test Explorer"]:
        print(f"\n--- Testing {npc_type} ---")
        result = runner.test_npc_filtering(npc_type)
        print(f"Player reputation view: {result['player_reputation_view']:.2f}")
        print(f"Cares about {len(result['relevant_actions'])} player actions")


async def demo_with_openai(api_key: str):
    """Demonstrate with OpenAI integration."""
    print("Running test with OpenAI...")
    
    runner = TestRunner()
    config = create_openai_config(api_key, "gpt-3.5-turbo")
    runner.set_ai_config(config)
    
    await runner.test_ai_integration("Test Trader", "Hello! I'm looking to do some trading.")


def demo_custom_scenario():
    """Demonstrate custom testing scenario."""
    print("Running custom scenario test...")
    
    runner = TestRunner()
    
    # Create a custom pirate NPC
    pirate = runner.create_custom_npc_test(
        name="Bloodthirsty Pete",
        npc_type=NPCType.PIRATE,
        background="A ruthless pirate who preys on traders in lawless systems.",
        custom_traits={"aggressive": 0.95, "greedy": 0.9, "helpful": 0.1}
    )
    
    # Modify scenario to be in a lawless system
    runner.modify_sample_data(
        system_info={"security_level": "Anarchy", "allegiance": None},
        player_actions=[
            {
                "type": "trade",
                "description": "Carrying 200 tons of valuable cargo",
                "location": "Lawless System",
                "value": 5000000.0
            }
        ]
    )
    
    # Test this scenario
    result = runner.test_npc_filtering("Bloodthirsty Pete")
    return result


if __name__ == "__main__":
    # Run basic demo
    demo_basic_test()
    
    # Uncomment to test with AI (requires API key)
    # asyncio.run(demo_with_openai("your-api-key-here"))
    
    # Test custom scenario
    demo_custom_scenario()