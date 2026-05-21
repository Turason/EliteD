"""
Elite Dangerous AI NPC System - Example Usage Script

This script demonstrates how to use the AI NPC system with various test scenarios.
Perfect for learning how the system works before connecting real game data.

Usage:
    python example_usage.py                    # Basic test without AI
    python example_usage.py --openai-key YOUR_KEY   # Test with OpenAI
    python example_usage.py --custom-scenario       # Test custom scenario
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import our module
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.append(src_path)

from ai_integration import (
    TestRunner, NPCType, EventType,
    create_openai_config, create_anthropic_config, create_local_config,
    quick_test, create_custom_npc_scenario
)
from data_ingestion import JournalIngestor


def _get_elite_data_path(custom_path: str = None) -> Path:
    """Resolve Elite Dangerous data directory path."""
    if custom_path:
        return Path(custom_path)
    return Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous"


def _get_latest_journal_file(ed_path: Path) -> Path:
    """Find the newest journal log in the Elite data folder."""
    journal_files = sorted(ed_path.glob("Journal*.log"), key=lambda p: p.stat().st_mtime)
    if not journal_files:
        raise FileNotFoundError(f"No journal files found in {ed_path}")
    return journal_files[-1]


def live_data_demo(ed_path: str = None):
    """Run filtering tests using real local journal and status data."""
    print("🛰️ LIVE DATA DEMO - Using local Elite Dangerous logs")
    print("=" * 50)

    resolved_path = _get_elite_data_path(ed_path)
    if not resolved_path.exists():
        print(f"❌ Elite data folder not found: {resolved_path}")
        print("💡 Use --ed-path to provide your game data folder.")
        return

    try:
        journal_file = _get_latest_journal_file(resolved_path)
    except FileNotFoundError as error:
        print(f"❌ {error}")
        return

    ingestor = JournalIngestor()
    runner = TestRunner()

    print(f"📂 Journal file: {journal_file.name}")
    player_status, system_state, summary = ingestor.ingest_journal_file(str(journal_file))

    status_file = resolved_path / "Status.json"
    if status_file.exists():
        player_status = ingestor.ingest_status_file(str(status_file), player_status)
        print("✅ Status.json loaded")
    else:
        print("ℹ️ Status.json not found, continuing with journal data only")

    # Feed ingested state directly into the existing runner model inputs.
    runner.sample_data["player_status"] = player_status
    runner.sample_data["system_state"] = system_state

    print("\nIngestion summary:")
    print(f"- Events read: {summary.events_read}")
    print(f"- Actions created: {summary.actions_created}")
    print(f"- Skipped events: {summary.skipped_events}")
    print(f"- Commander: {player_status.name}")
    print(f"- Location: {player_status.current_system}/{player_status.current_station or 'In Space'}")

    print("\nTesting NPC reactions to your real recent activity...")
    npc_types = ["Test Trader", "Test Pirate", "Test Explorer"]
    for npc_type in npc_types:
        print(f"\n--- {npc_type} ---")
        result = runner.test_npc_filtering(npc_type)
        print(f"💭 Opinion of player: {result['player_reputation_view']:.2f}")
        print(f"📋 Relevant actions: {len(result['relevant_actions'])}")

    print("\n✅ Live data demo complete!")


def basic_demo():
    """Demonstrate basic functionality without AI."""
    print("🚀 BASIC DEMO - No AI Required")
    print("=" * 50)
    
    runner = TestRunner()
    
    print("\n1. Testing different NPC types...")
    
    # Test each NPC type
    npc_types = ["Test Trader", "Test Pirate", "Test Explorer"]
    
    for npc_type in npc_types:
        print(f"\n--- {npc_type} ---")
        result = runner.test_npc_filtering(npc_type)
        
        print(f"💭 Opinion of player: {result['player_reputation_view']:.2f}")
        print(f"📋 Cares about {len(result['relevant_actions'])} of your recent actions")
        print(f"📰 Interested in {len(result['relevant_news'])} news items")
        
        # Show most relevant action
        if result['relevant_actions']:
            top_action = result['relevant_actions'][0]
            print(f"🎯 Most relevant action: {top_action['action'][:50]}...")
            print(f"   Sentiment: {top_action['sentiment']:.2f}")
    
    print(f"\n✅ Basic demo complete! Try with AI for actual conversations.")


async def ai_demo(api_key: str, provider: str = "openai"):
    """Demonstrate with AI integration."""
    print(f"🤖 AI DEMO - Using {provider.upper()}")
    print("=" * 50)
    
    # Create AI configuration
    if provider.lower() == "openai":
        config = create_openai_config(api_key)
    elif provider.lower() == "anthropic":
        config = create_anthropic_config(api_key)
    else:
        config = create_local_config()
    
    runner = TestRunner(config)
    
    print("\n1. Testing AI conversations with different NPCs...")
    
    # Test conversations
    conversations = [
        ("Test Trader", "Hello! I'm looking to do some profitable trading."),
        ("Test Pirate", "Well, well... what do we have here?"),
        ("Test Explorer", "I've been exploring the outer rim. Any interesting discoveries lately?")
    ]
    
    for npc_name, message in conversations:
        print(f"\n--- Conversation with {npc_name} ---")
        print(f"👨‍🚀 Player says: \"{message}\"")
        
        try:
            response = await runner.test_ai_integration(npc_name, message)
            if response:
                print(f"🎭 {npc_name}: {response}")
            else:
                print("❌ Failed to get AI response")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()  # Add spacing between conversations
    
    print("✅ AI demo complete!")


def custom_scenario_demo():
    """Demonstrate custom scenario testing."""
    print("🎨 CUSTOM SCENARIO DEMO")
    print("=" * 50)
    
    runner = TestRunner()
    
    print("\n1. Creating a custom pirate encounter...")
    
    # Create a bloodthirsty pirate
    pirate = runner.create_custom_npc_test(
        name="Captain Blackbeard",
        npc_type=NPCType.PIRATE,
        background="A notorious pirate captain who rules the lawless systems with an iron fist. Known for taking valuable cargo and leaving no witnesses.",
        custom_traits={
            "aggressive": 0.95,
            "greedy": 0.90,
            "ruthless": 0.85,
            "helpful": 0.05
        },
        custom_attitudes={
            "Federation": -0.9,
            "Empire": -0.8,
            "Alliance": -0.7,
            "Pirates": 0.9
        }
    )
    
    print("\n2. Setting up a dangerous scenario...")
    
    # Modify the scenario - player is carrying valuable cargo in a lawless system
    runner.modify_sample_data(
        system_info={
            "name": "Blackbeard's Haven",
            "security_level": "Anarchy",
            "allegiance": None,
            "controlling_faction": "Blackbeard's Crew"
        },
        player_actions=[
            {
                "type": "trade",
                "description": "Loaded 300 tons of rare Imperial Slaves worth 15 million credits",
                "location": "Imperial Space",
                "value": 15000000.0,
                "target": "Empire"
            },
            {
                "type": "jump",
                "description": "Jumped into the anarchic Blackbeard's Haven system",
                "location": "Blackbeard's Haven"
            }
        ],
        news=[
            "Imperial Slave Trade Routes Under Pirate Attack",
            "Federal Navy Pulls Back from Lawless Systems",
            "Cargo Ships Advised to Avoid Outer Rim"
        ]
    )
    
    print("\n3. Testing pirate's reaction to this scenario...")
    
    result = runner.test_npc_filtering("Captain Blackbeard")
    
    print(f"\n🏴‍☠️ Captain Blackbeard's Assessment:")
    print(f"💰 Interest in player: {result['player_reputation_view']:.2f}")
    print(f"🎯 Relevant actions noticed: {len(result['relevant_actions'])}")
    
    print(f"\n📋 What caught his attention:")
    for i, action in enumerate(result['relevant_actions'][:3]):
        sentiment_emoji = "😈" if action['sentiment'] > 0 else "😐" if action['sentiment'] == 0 else "😒"
        print(f"   {i+1}. {action['action']} {sentiment_emoji}")
        print(f"      Sentiment: {action['sentiment']:.2f}")
    
    print(f"\n📰 News that interests him:")
    for news, sentiment in result['relevant_news'][:2]:
        sentiment_emoji = "😈" if sentiment > 0 else "😐" if sentiment == 0 else "😒"
        print(f"   • {news} {sentiment_emoji}")
    
    print(f"\n✅ Custom scenario complete!")
    print(f"💡 Tip: Run with --ai to see how Captain Blackbeard would actually talk to you!")


def interactive_demo(api_key=None, provider="openai"):
    """Interactive demo where user can chat with NPCs."""
    print("💬 INTERACTIVE DEMO")
    print("=" * 50)
    print("Chat with different NPCs! Type 'quit' to exit or 'switch' to change NPCs.")
    
    npc_options = ["Test Trader", "Test Pirate", "Test Explorer"]
    current_npc = npc_options[0]
    
    runner = TestRunner()
    
    # Check if AI is configured
    ai_configured = False
    if api_key:
        # Use provided API key
        if provider.lower() == "openai":
            config = create_openai_config(api_key)
        elif provider.lower() == "anthropic":
            config = create_anthropic_config(api_key)
        else:
            config = create_local_config()
        runner.set_ai_config(config)
        ai_configured = True
        print(f"🤖 AI detected ({provider.upper()})! You can have real conversations.")
    elif os.getenv('OPENAI_API_KEY'):
        config = create_openai_config(os.getenv('OPENAI_API_KEY'))
        runner.set_ai_config(config)
        ai_configured = True
        print("🤖 AI detected! You can have real conversations.")
    else:
        print("ℹ️  No AI configured. Responses will be simulated.")
    
    print(f"\n👋 Currently talking to: {current_npc}")
    print("Type your message:")
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() in ['switch', 'change']:
                print("Available NPCs:")
                for i, npc in enumerate(npc_options):
                    print(f"  {i+1}. {npc}")
                
                try:
                    choice = int(input("Choose NPC (number): ")) - 1
                    if 0 <= choice < len(npc_options):
                        current_npc = npc_options[choice]
                        print(f"👋 Now talking to: {current_npc}")
                    else:
                        print("Invalid choice!")
                except ValueError:
                    print("Please enter a number!")
                continue
            
            elif not user_input:
                continue
            
            # Get response
            if ai_configured:
                try:
                    response = asyncio.run(runner.test_ai_integration(current_npc, user_input))
                    if response:
                        print(f"\n🎭 {current_npc}: {response}")
                    else:
                        print("❌ Failed to get AI response")
                except Exception as e:
                    print(f"❌ AI Error: {e}")
            else:
                # Simulated response
                result = runner.test_npc_filtering(current_npc)
                if result['player_reputation_view'] > 0:
                    print(f"\n🎭 {current_npc}: [This NPC likes you and would respond positively]")
                else:
                    print(f"\n🎭 {current_npc}: [This NPC is cautious/hostile toward you]")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


def main():
    """Main function with command line argument handling."""
    parser = argparse.ArgumentParser(description="Elite Dangerous AI NPC System Demo")
    
    parser.add_argument("--openai-key", help="OpenAI API key for AI testing")
    parser.add_argument("--anthropic-key", help="Anthropic API key for AI testing")
    parser.add_argument("--local", action="store_true", help="Use local AI model (Ollama)")
    parser.add_argument("--custom-scenario", action="store_true", help="Run custom scenario demo")
    parser.add_argument("--interactive", action="store_true", help="Interactive chat mode")
    parser.add_argument("--quick", help="Quick test with NPC type (trader, pirate, explorer)")
    parser.add_argument("--live-data", action="store_true", help="Use real local journal/status data")
    parser.add_argument("--ed-path", help="Path to Elite Dangerous journal folder")
    
    args = parser.parse_args()
    
    print("🌌 ELITE DANGEROUS AI NPC SYSTEM")
    print("=" * 60)
    
    # Quick test
    if args.quick:
        api_key = args.openai_key or args.anthropic_key
        provider = "anthropic" if args.anthropic_key else "openai"
        result = quick_test(args.quick, api_key, provider)
        return
    
    # Interactive mode
    if args.interactive:
        api_key = args.openai_key or args.anthropic_key
        provider = "anthropic" if args.anthropic_key else "openai"
        interactive_demo(api_key, provider)
        return
    
    # Custom scenario
    if args.custom_scenario:
        custom_scenario_demo()
        return

    # Local journal/status data mode
    if args.live_data:
        live_data_demo(args.ed_path)
        return
    
    # Basic demo (always run)
    basic_demo()
    
    # AI demo if key provided
    if args.openai_key:
        print("\n" + "=" * 60)
        asyncio.run(ai_demo(args.openai_key, "openai"))
    elif args.anthropic_key:
        print("\n" + "=" * 60)
        asyncio.run(ai_demo(args.anthropic_key, "anthropic"))
    elif args.local:
        print("\n" + "=" * 60)
        asyncio.run(ai_demo("", "local"))
    
    print("\n🎯 NEXT STEPS:")
    print("1. Try with --openai-key YOUR_KEY for actual AI conversations")
    print("2. Try --custom-scenario for advanced testing")
    print("3. Try --interactive for chat mode")
    print("4. Try --live-data to ingest your real Elite Dangerous logs")
    print("5. Build a user interface for the chatbot")


if __name__ == "__main__":
    main()