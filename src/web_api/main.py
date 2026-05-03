"""
FastAPI Web Service for Elite Dangerous AI NPC System

This provides REST API endpoints for testing the AI NPC system with
automatic interactive documentation at http://127.0.0.1:8000/docs

Endpoints:
- GET /npcs - List available NPC types
- POST /test-filtering - Test NPC filtering with scenario data
- POST /build-context - Build conversation context for an NPC
- POST /chat - Chat with an NPC (requires AI configuration)
- POST /custom-npc - Create a custom NPC
- GET /sample-data - Get sample test data
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import os
import sys

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

from ai_integration import (
    TestRunner, NPCFilter, ContextBuilder, 
    NPCType, EventType, PlayerAction, PlayerStatus, SystemState, GalacticNews,
    NPCPersonality, create_openai_config, create_anthropic_config, create_local_config,
    AIProvider
)

# FastAPI app
app = FastAPI(
    title="Elite Dangerous AI NPC System",
    description="Interactive API for testing AI-powered NPCs that react to player actions and galactic events",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at http://127.0.0.1:8000/docs
    redoc_url="/redoc"  # ReDoc at http://127.0.0.1:8000/redoc
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global test runner instance
test_runner = TestRunner()

# Pydantic models for API requests/responses
class PlayerActionRequest(BaseModel):
    event_type: str = Field(..., description="Type of event (trade, combat, exploration, etc.)")
    description: str = Field(..., description="Human readable description of the action")
    location: Optional[str] = Field(None, description="Where the action took place")
    target: Optional[str] = Field(None, description="Target of the action (faction, ship type, etc.)")
    value: Optional[float] = Field(None, description="Credit value or other numeric value")


class SystemStateRequest(BaseModel):
    name: str = Field("Sol", description="System name")
    allegiance: Optional[str] = Field(None, description="System allegiance (Federation, Empire, Alliance)")
    security_level: str = Field("Medium", description="Security level (High, Medium, Low, Anarchy)")
    controlling_faction: Optional[str] = Field(None, description="Controlling faction name")
    active_conflicts: List[str] = Field(default_factory=list, description="Active conflicts in system")


class TestScenarioRequest(BaseModel):
    npc_name: str = Field("Test Trader", description="Name of NPC to test")
    npc_type: Optional[str] = Field(None, description="Type of NPC (trader, pirate, explorer)")
    player_actions: List[PlayerActionRequest] = Field(default_factory=list, description="Recent player actions")
    system_state: SystemStateRequest = Field(default_factory=SystemStateRequest, description="Current system state")
    galactic_news: List[str] = Field(default_factory=list, description="Recent galactic news headlines")


class CustomNPCRequest(BaseModel):
    name: str = Field(..., description="Name for the custom NPC")
    npc_type: str = Field(..., description="Base NPC type (trader, pirate, explorer, etc.)")
    background: str = Field(..., description="Background story for the NPC")
    interest_weights: Optional[Dict[str, float]] = Field(None, description="What events this NPC cares about (0.0-1.0)")
    faction_attitudes: Optional[Dict[str, float]] = Field(None, description="NPC attitudes toward factions (-1.0 to 1.0)")
    personality_traits: Optional[Dict[str, float]] = Field(None, description="Personality traits (0.0-1.0)")


class ChatRequest(BaseModel):
    npc_name: str = Field("Test Trader", description="Name of NPC to chat with")
    message: str = Field(..., description="Message to send to the NPC")
    ai_provider: str = Field("openai", description="AI provider (openai, anthropic, local)")
    ai_model: str = Field("gpt-3.5-turbo", description="AI model to use")
    api_key: Optional[str] = Field(None, description="API key for AI service")
    scenario: Optional[TestScenarioRequest] = Field(None, description="Custom scenario for the conversation")


class AIConfigRequest(BaseModel):
    provider: str = Field("openai", description="AI provider (openai, anthropic, local)")
    api_key: Optional[str] = Field(None, description="API key for commercial providers")
    model: str = Field("gpt-3.5-turbo", description="Model name to use")
    max_tokens: int = Field(500, description="Maximum tokens for AI response")
    temperature: float = Field(0.8, description="AI creativity (0.0-1.0)")


class QuickTestRequest(BaseModel):
    scenario_type: str = Field("peaceful_trader", description="Type of scenario: peaceful_trader or dangerous_pirate")
    npc_type: str = Field("trader", description="Type of NPC: trader, pirate, explorer, etc.")
    include_ai_response: bool = Field(False, description="Generate actual AI response (requires AI configured)")


# API Endpoints

@app.get("/", summary="API Information")
async def root():
    """API root - provides basic information about the service."""
    return {
        "title": "Elite Dangerous AI NPC System",
        "version": "1.0.0",
        "description": "REST API for testing AI-powered NPCs",
        "docs_url": "/docs",
        "endpoints": {
            "list_npcs": "GET /npcs",
            "test_filtering": "POST /test-filtering", 
            "build_context": "POST /build-context",
            "chat_with_npc": "POST /chat",
            "create_custom_npc": "POST /custom-npc",
            "sample_data": "GET /sample-data"
        }
    }


@app.get("/npcs", summary="List Available NPCs")
async def list_npcs():
    """Get list of available NPC types and templates."""
    npc_types = [npc_type.value for npc_type in NPCType]
    templates = {
        "trader": "Merchant focused on profit and safe trade routes",
        "pirate": "Dangerous outlaw who preys on merchants and cargo ships", 
        "explorer": "Seasoned explorer seeking unknown reaches of the galaxy",
        "bounty_hunter": "Professional hunter tracking wanted criminals",
        "federal_navy": "Federal military officer devoted to Federation ideals",
        "imperial_navy": "Imperial officer serving the Empire",
        "alliance": "Alliance representative promoting cooperation",
        "engineer": "Brilliant engineer researching ship modifications",
        "citizen": "Regular civilian living in inhabited systems"
    }
    
    return {
        "available_types": npc_types,
        "templates": templates,
        "default_npcs": ["Test Trader", "Test Pirate", "Test Explorer"]
    }


@app.post("/test-filtering", summary="Test NPC Filtering")
async def test_npc_filtering(scenario: TestScenarioRequest):
    """
    Test how an NPC filters and reacts to player actions and galactic events.
    Returns what the NPC cares about and their sentiment toward each item.
    """
    try:
        # Convert request to internal models
        if scenario.player_actions:
            actions = []
            for action_req in scenario.player_actions:
                try:
                    event_type = EventType(action_req.event_type.lower())
                except ValueError:
                    # Default to trade if unknown event type
                    event_type = EventType.TRADE
                
                action = PlayerAction(
                    event_type=event_type,
                    description=action_req.description,
                    timestamp="2024-03-29T12:00:00Z",
                    location=action_req.location,
                    target=action_req.target,
                    value=action_req.value
                )
                actions.append(action)
            
            # Update test runner with custom actions
            test_runner.sample_data["player_status"].recent_actions = actions
        
        # Update system state if provided
        if scenario.system_state:
            sys_state = test_runner.sample_data["system_state"]
            sys_state.name = scenario.system_state.name
            sys_state.allegiance = scenario.system_state.allegiance
            sys_state.security_level = scenario.system_state.security_level
            sys_state.controlling_faction = scenario.system_state.controlling_faction
            sys_state.active_conflicts = scenario.system_state.active_conflicts
        
        # Update news if provided
        if scenario.galactic_news:
            test_runner.sample_data["galactic_news"].galnet_headlines = scenario.galactic_news
        
        # Run the filtering test
        result = test_runner.test_npc_filtering(scenario.npc_name)
        
        return {
            "npc_name": result["npc_name"],
            "npc_type": result["npc_type"],
            "overall_opinion": result["player_reputation_view"],
            "opinion_description": _get_opinion_description(result["player_reputation_view"]),
            "relevant_actions": result["relevant_actions"],
            "relevant_news": result["relevant_news"],
            "system_views": result["system_views"],
            "summary": {
                "actions_noticed": len(result["relevant_actions"]),
                "news_interested": len(result["relevant_news"]),
                "system_opinions": len(result["system_views"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing scenario: {str(e)}")


@app.post("/build-context", summary="Build Conversation Context")
async def build_context(scenario: TestScenarioRequest):
    """
    Build the complete conversation context that would be sent to an AI.
    Shows the system prompt, user prompt, and filtered data.
    """
    try:
        # Process scenario (same as test_filtering)
        if scenario.player_actions:
            actions = []
            for action_req in scenario.player_actions:
                try:
                    event_type = EventType(action_req.event_type.lower())
                except ValueError:
                    event_type = EventType.TRADE
                
                action = PlayerAction(
                    event_type=event_type,
                    description=action_req.description,
                    timestamp="2024-03-29T12:00:00Z",
                    location=action_req.location,
                    target=action_req.target,
                    value=action_req.value
                )
                actions.append(action)
            
            test_runner.sample_data["player_status"].recent_actions = actions
        
        # Build context
        prompts = test_runner.test_context_building(scenario.npc_name)
        
        return {
            "npc_name": scenario.npc_name,
            "system_prompt": prompts["system"],
            "user_prompt": prompts["user"],
            "context_data": prompts["context_data"],
            "prompt_stats": {
                "system_prompt_length": len(prompts["system"]),
                "user_prompt_length": len(prompts["user"]),
                "total_length": len(prompts["system"]) + len(prompts["user"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error building context: {str(e)}")


@app.post("/chat", summary="Chat with NPC")
async def chat_with_npc(chat_request: ChatRequest):
    """
    Have a conversation with an NPC. Requires AI configuration.
    Returns the NPC's response and metadata about the conversation.
    """
    try:
        # Configure AI if credentials provided
        if chat_request.api_key or chat_request.ai_provider == "local":
            if chat_request.ai_provider == "openai":
                config = create_openai_config(chat_request.api_key, chat_request.ai_model)
            elif chat_request.ai_provider == "anthropic":
                config = create_anthropic_config(chat_request.api_key, chat_request.ai_model) 
            elif chat_request.ai_provider == "local":
                config = create_local_config(chat_request.ai_model)
            else:
                raise HTTPException(status_code=400, detail="Unsupported AI provider")
            
            test_runner.set_ai_config(config)
        
        # Process custom scenario if provided
        if chat_request.scenario:
            scenario = chat_request.scenario
            if scenario.player_actions:
                actions = []
                for action_req in scenario.player_actions:
                    try:
                        event_type = EventType(action_req.event_type.lower())
                    except ValueError:
                        event_type = EventType.TRADE
                    
                    action = PlayerAction(
                        event_type=event_type,
                        description=action_req.description,
                        timestamp="2024-03-29T12:00:00Z",
                        location=action_req.location,
                        target=action_req.target,
                        value=action_req.value
                    )
                    actions.append(action)
                
                test_runner.sample_data["player_status"].recent_actions = actions
        
        # Generate AI response
        if not test_runner.ai_service:
            raise HTTPException(
                status_code=400, 
                detail="AI service not configured. Provide api_key and ai_provider."
            )
        
        response = await test_runner.test_ai_integration(chat_request.npc_name, chat_request.message)
        
        if not response:
            raise HTTPException(status_code=500, detail="Failed to generate AI response")
        
        return {
            "npc_name": chat_request.npc_name,
            "user_message": chat_request.message,
            "npc_response": response,
            "ai_provider": chat_request.ai_provider,
            "ai_model": chat_request.ai_model,
            "timestamp": "2024-03-29T12:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/custom-npc", summary="Create Custom NPC")
async def create_custom_npc(npc_request: CustomNPCRequest):
    """
    Create a custom NPC with specific personality traits and interests.
    Returns the created NPC details and tests it with default scenario.
    """
    try:
        # Convert string npc_type to enum
        try:
            npc_type_enum = NPCType(npc_request.npc_type.lower())
        except ValueError:
            npc_type_enum = NPCType.TRADER
        
        # Convert interest weights from strings to EventType enums
        interest_weights = {}
        if npc_request.interest_weights:
            for event_str, weight in npc_request.interest_weights.items():
                try:
                    event_type = EventType(event_str.lower())
                    interest_weights[event_type] = weight
                except ValueError:
                    continue
        
        # Create the custom NPC
        npc = test_runner.create_custom_npc_test(
            name=npc_request.name,
            npc_type=npc_type_enum,
            background=npc_request.background,
            custom_interests=interest_weights if interest_weights else None,
            custom_attitudes=npc_request.faction_attitudes,
            custom_traits=npc_request.personality_traits
        )
        
        # Test the NPC with default scenario
        test_result = test_runner.test_npc_filtering(npc_request.name)
        
        return {
            "created_npc": {
                "name": npc.name,
                "type": npc.npc_type.value,
                "background": npc.background_story,
                "interest_weights": {event.value: weight for event, weight in npc.interest_weights.items()},
                "faction_attitudes": npc.faction_attitudes,
                "personality_traits": npc.personality_traits
            },
            "test_result": {
                "overall_opinion": test_result["player_reputation_view"],
                "relevant_actions": len(test_result["relevant_actions"]),
                "relevant_news": len(test_result["relevant_news"])
            },
            "status": "NPC created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating NPC: {str(e)}")


@app.get("/sample-data", summary="Get Sample Test Data")
async def get_sample_data():
    """Get sample player actions, system state, and news for testing."""
    return {
        "player_actions": [
            {
                "event_type": "trade",
                "description": "Sold 50 tons of gold for 2.5 million credits",
                "location": "Jameson Memorial",
                "value": 2500000.0
            },
            {
                "event_type": "combat", 
                "description": "Destroyed wanted Anaconda pirate",
                "location": "Wolf 359",
                "target": "Pirates",
                "value": 850000.0
            },
            {
                "event_type": "exploration",
                "description": "Discovered Earth-like world",
                "location": "Unexplored System",
                "value": 1200000.0
            },
            {
                "event_type": "reputation_gain",
                "description": "Completed Federal Navy mission",
                "target": "Federation"
            }
        ],
        "system_states": [
            {
                "name": "Sol",
                "allegiance": "Federation",
                "security_level": "High",
                "controlling_faction": "Federal Congress"
            },
            {
                "name": "Pirate Haven",
                "allegiance": None,
                "security_level": "Anarchy",
                "controlling_faction": "Crimson Fleet"
            },
            {
                "name": "Explorer's Rest",
                "allegiance": "Alliance",
                "security_level": "Medium",
                "controlling_faction": "Independent Explorers"
            }
        ],
        "galactic_news": [
            "Federal Navy Reports Increased Thargoid Activity",
            "New Trade Route Opens Between Sol and Shinrarta Dezhra",
            "Imperial Wedding Celebrations Begin",
            "Alliance Explores New Terraforming Technology",
            "Pirate Activity Increases in Outer Rim Systems",
            "Community Goal: Build New Starport in Colonia"
        ]
    }


@app.post("/configure-ai", summary="Configure AI Service") 
async def configure_ai_service(ai_config: AIConfigRequest):
    """Configure the AI service for chat functionality."""
    try:
        if ai_config.provider == "openai":
            config = create_openai_config(ai_config.api_key, ai_config.model)
        elif ai_config.provider == "anthropic":
            config = create_anthropic_config(ai_config.api_key, ai_config.model)
        elif ai_config.provider == "local":
            config = create_local_config(ai_config.model)
        else:
            raise HTTPException(status_code=400, detail="Unsupported AI provider")
        
        config.max_tokens = ai_config.max_tokens
        config.temperature = ai_config.temperature
        
        test_runner.set_ai_config(config)
        
        return {
            "status": "AI service configured successfully",
            "provider": ai_config.provider,
            "model": ai_config.model,
            "max_tokens": ai_config.max_tokens,
            "temperature": ai_config.temperature
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")


@app.get("/system-status", summary="Get System Status")
async def get_system_status():
    """
    Get current status of the AI NPC system including available services.
    This endpoint will automatically appear in the /docs interface!
    """
    ai_configured = test_runner.ai_service is not None
    
    return {
        "system_name": "Elite Dangerous AI NPC System",
        "version": "1.0.0",
        "status": "running",
        "ai_service_configured": ai_configured,
        "available_endpoints": [
            "GET /npcs - List NPCs",
            "POST /test-filtering - Test reactions",
            "POST /build-context - Build prompts", 
            "POST /chat - Chat with NPCs",
            "POST /custom-npc - Create custom NPCs",
            "GET /sample-data - Sample test data",
            "GET /system-status - This endpoint!"
        ],
        "documentation_urls": {
            "interactive": "http://127.0.0.1:8000/docs",
            "redoc": "http://127.0.0.1:8000/redoc"
        }
    }


@app.post("/quick-test", summary="Quick NPC Test")
async def quick_npc_test(test_request: QuickTestRequest):
    """
    Quick test endpoint that demonstrates automatic request validation.
    FastAPI automatically validates the JSON request against the QuickTestRequest model!
    """
    try:
        # This endpoint will automatically appear in /docs with a form to fill out!
        scenarios = {
            "peaceful_trader": {
                "player_actions": [
                    {
                        "event_type": "trade",
                        "description": "Successful profitable trade run",
                        "value": 1000000.0
                    }
                ]
            },
            "dangerous_pirate": {
                "player_actions": [
                    {
                        "event_type": "combat", 
                        "description": "Destroyed several security ships",
                        "target": "System Authority"
                    }
                ]
            }
        }
        
        scenario_data = scenarios.get(test_request.scenario_type, scenarios["peaceful_trader"])
        
        # Test basic NPC filtering
        filtering_result = test_runner.test_npc_filtering(f"Test {test_request.npc_type.title()}")
        
        result = {
            "test_type": test_request.scenario_type,
            "npc_type": test_request.npc_type,
            "npc_opinion": filtering_result["player_reputation_view"],
            "relevant_actions": len(filtering_result["relevant_actions"]),
            "scenario_used": scenario_data
        }
        
        # If AI response requested, add that too
        if test_request.include_ai_response and test_runner.ai_service:
            ai_response = await test_runner.test_ai_integration(
                f"Test {test_request.npc_type.title()}", 
                "Hello! How are things going?"
            )
            result["ai_response"] = ai_response
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Quick test error: {str(e)}")


# Utility functions
def _get_opinion_description(sentiment: float) -> str:
    """Convert sentiment score to human-readable description."""
    if sentiment > 0.7:
        return "Very Positive - Highly impressed with this Commander"
    elif sentiment > 0.3:
        return "Positive - Generally favorable impression" 
    elif sentiment > -0.3:
        return "Neutral - No strong opinion yet"
    elif sentiment > -0.7:
        return "Negative - Some concerns about this Commander"
    else:
        return "Very Negative - Views this Commander with suspicion or hostility"


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Elite Dangerous AI NPC API Server...")
    print("📖 Interactive API docs will be available at: http://127.0.0.1:8000/docs")
    print("📚 Alternative docs at: http://127.0.0.1:8000/redoc")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")