# Elite Dangerous AI NPC Chatbot System

An AI-powered chatbot system that creates immersive NPC interactions for Elite Dangerous, reacting intelligently to player actions, galactic events, and current game state.

## 🎯 Project Vision

Create believable NPCs that:
- React differently based on their personality (trader vs pirate vs explorer)
- Remember and care about your recent actions
- Have opinions about galactic news and events 
- View you differently based on your reputation and behavior
- Provide immersive, lore-appropriate conversations

## 🏗️ Architecture Overview

### Current Status: ✅ AI Integration Layer (Complete)
- **NPCFilter**: Determines what each NPC cares about and their sentiment
- **ContextBuilder**: Assembles game data into rich AI prompts
- **AIService**: Interfaces with OpenAI, Anthropic, or local AI models
- **TestRunner**: Test system with constructed data

### Current Status: ✅ Initial Data Ingestion Slice (Implemented)
- **JournalIngestor**: Parses local Elite Dangerous journal logs and maps data into existing models
- **Status Support**: Reads `Status.json` and applies current-state updates
- **Live Demo Mode**: Runs NPC filtering using your real local game data

### Planned Modules:
1. **Data Collection Layer** - Monitor journal files, fetch market/news data
2. **Database Layer** - SQLite storage for all game data
3. **User Interface** - Chat interface to talk with NPCs
4. **Configuration Management** - Easy setup and NPC customization

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Basic Test (No AI Required)
```bash
python example_usage.py
```

### 3. Test with AI (Requires API Key)
```bash
# With OpenAI
python example_usage.py --openai-key YOUR_OPENAI_KEY

# With Anthropic Claude
python example_usage.py --anthropic-key YOUR_ANTHROPIC_KEY

# With local model (requires Ollama or similar)
python example_usage.py --local
```

### 4. Interactive Chat Mode
```bash
python example_usage.py --interactive --openai-key YOUR_KEY
```

### 5. Custom Scenarios
```bash
python example_usage.py --custom-scenario
```

### 6. Test with Real Local Game Data (No API Keys Needed)
```bash
# Uses default Windows Elite folder:
python example_usage.py --live-data

# Or provide an explicit path:
python example_usage.py --live-data --ed-path "C:/Users/<you>/Saved Games/Frontier Developments/Elite Dangerous"
```

## 🎮 Example Usage

```python
from ai_integration import TestRunner, create_openai_config, NPCType

# Basic testing without AI
runner = TestRunner()
result = runner.test_npc_filtering("Test Trader")
print(f"Trader's opinion of player: {result['player_reputation_view']}")

# Testing with AI
config = create_openai_config("your-api-key-here")
runner = TestRunner(config)

# Have a conversation
response = await runner.test_ai_integration(
    "Test Pirate", 
    "I've been hunting bounties in this system."
)
print(f"Pirate says: {response}")
```

## 🎭 NPC Types & Personalities

Currently implemented:

- **Traders**: Care about trade routes, cargo, market prices
- **Pirates**: Interested in combat, valuable cargo, wanted players  
- **Explorers**: Love discovery, jump ranges, exploration data
- **Bounty Hunters**: Focus on combat, wanted ships, law enforcement
- **Military NPCs**: Concerned with faction allegiance, conflicts
- **Engineers**: Interested in rare materials, technology

Each NPC has:
- **Interest Weights**: What types of events they care about
- **Faction Attitudes**: How they view Federation/Empire/Alliance
- **Personality Traits**: Aggressive, helpful, greedy, cautious, etc.

## 📊 How It Works

1. **Data Filtering**: Each NPC filters your actions through their personality
   - Traders love hearing about successful trades
   - Pirates are interested in your cargo and combat history
   - Faction allegiance affects how they view your reputation gains/losses

2. **Sentiment Analysis**: NPCs assign emotional reactions to events
   - -1.0 = Very Negative (hostile, disapproving) 
   - 0.0 = Neutral (indifferent)
   - +1.0 = Very Positive (impressed, approving)

3. **Context Building**: Relevant data is assembled into rich prompts
   - NPC personality and background
   - Your recent actions that matter to them
   - Current system state and galactic news
   - Their overall opinion of you

4. **AI Generation**: The AI roleplay as the NPC with full context

## 🧪 Testing Features

### Built-in Test Scenarios
- **Default Scenario**: Typical commander with mixed recent actions
- **Custom NPCs**: Create NPCs with specific personalities
- **Custom Scenarios**: Modify player actions, system state, news

### Test Different Situations
```python
# Create a paranoid pirate in lawless space
runner = create_custom_npc_scenario(
    npc_name="Bloodthirsty Pete",
    npc_type=NPCType.PIRATE,
    background="Ruthless pirate who preys on cargo ships",
    player_actions=[{
        "type": "trade",
        "description": "Carrying 200 tons of valuable Imperial Slaves",
        "location": "Lawless System", 
        "value": 15000000.0
    }],
    system_name="Pirate Haven",
    security_level="Anarchy"
)
```

## ⚙️ Configuration

### Environment Variables
```bash
# OpenAI
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Local AI (Ollama, etc.)
LOCAL_AI_BASE_URL=http://localhost:11434
LOCAL_AI_MODEL=llama2

# Optional settings
AI_MAX_TOKENS=500
AI_TEMPERATURE=0.8
LOG_LEVEL=INFO
```

### AI Model Recommendations
- **Creative Roleplay**: GPT-4, Claude-3-Opus (higher temperature)
- **Consistent Characters**: GPT-3.5-Turbo, Claude-3-Sonnet  
- **Budget Friendly**: GPT-3.5-Turbo, Claude-3-Haiku

## 🔧 Development Status

- ✅ **AI Integration Layer**: Complete and tested
- ✅ **Data Collection (Initial Local Ingestion)**: Implemented (journal + status)
- 🚧 **Data Collection (Online Enrichment)**: Not yet implemented
- 🚧 **Database Storage**: Not yet implemented
- 🚧 **User Interface**: Not yet implemented
- 🚧 **Real-time Continuous Monitoring**: Not yet implemented

## 📁 Project Structure

```
EliteD/
├── src/
│   ├── ai_integration/          # ✅ AI integration module
│   │   ├── models.py            # Data structures
│   │   ├── npc_filter.py        # NPC personality filtering  
│   │   ├── context_builder.py   # AI prompt generation
│   │   ├── ai_service.py        # AI provider interfaces
│   │   ├── test_runner.py       # Testing framework
│   │   ├── config.py            # Configuration management
│   │   └── __init__.py          # Package initialization
│   └── data_ingestion/          # ✅ Local data ingestion (initial)
│       ├── journal_ingestor.py  # Journal/Status parsing to models
│       └── __init__.py          # Ingestion exports
├── example_usage.py             # ✅ Example scripts and demos
├── requirements.txt             # ✅ Python dependencies
└── README.md                    # ✅ This file
```

## 📥 Local Data Ingestion Details

The ingestion module maps game data directly into your existing model layer:

- **Input files**:
    - `Journal*.log` (line-delimited JSON events)
    - `Status.json` (current cockpit/game state snapshot)
- **Mapped output models**:
    - `PlayerStatus`
    - `SystemState`
    - `PlayerAction` (appended to `recent_actions`)

### Currently mapped journal events (initial slice)
- `LoadGame`
- `Location`, `FSDJump`, `CarrierJump`
- `Docked`, `Undocked`
- `Rank`, `Reputation`
- Mission events: `MissionAccepted`, `MissionCompleted`, `MissionFailed`
- Trade events: `MarketBuy`, `MarketSell`, `BuyDrones`, `SellDrones`
- Combat events: `Bounty`, `FactionKillBond`, `Died`, `Interdicted`, `EscapeInterdiction`
- Exploration events: `Scan`, `ScanOrganic`, `CodexEntry`, `SellExplorationData`

### Note
- No game login credentials are needed for local journal/status ingestion.
- API keys are only needed when generating AI responses with OpenAI/Anthropic.

## 🎯 Next Steps

1. **Test the current system** with your favorite scenarios
2. **Try different NPC personalities** and see how they react
3. **Experiment with AI models** to find your preferred style
4. **Plan the database schema** for storing game data
5. **Design the journal monitoring system** for real-time data
6. **Create the user interface** for easy NPC conversations

## 💡 Tips for Testing

1. **Start without AI** to understand the filtering system
2. **Test extreme scenarios** (hostile pirates, Empire vs Federation)
3. **Create custom NPCs** with specific interests and attitudes  
4. **Try different AI models** and temperatures for varied personalities
5. **Monitor token usage** and costs when using commercial APIs

## 🤝 Contributing

This is a learning project! Feel free to:
- Experiment with NPC personalities
- Add new event types or data sources
- Improve the prompt generation
- Test edge cases and report issues
- Suggest new features

---

**Ready to create immersive Elite Dangerous NPCs?** Start with `python example_usage.py` and begin your journey into AI-powered space conversations! 🚀