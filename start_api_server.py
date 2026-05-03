"""
Start the Elite Dangerous AI NPC Web API Server

This script starts the FastAPI server with automatic interactive documentation.
Access the API at: http://127.0.0.1:8000/docs
"""

import os
import sys

def install_dependencies():
    """Install required dependencies for the web API."""
    print("📦 Installing web API dependencies...")
    os.system("pip install fastapi uvicorn pydantic")
    print("✅ Dependencies installed!")

def start_server():
    """Start the FastAPI server."""
    # Add src directory to Python path
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_path)
    
    try:
        import uvicorn
        from web_api.main import app
        
        print("🚀 ELITE DANGEROUS AI NPC API SERVER")
        print("=" * 50)
        print("📖 Interactive API Documentation:")
        print("   http://127.0.0.1:8000/docs")
        print("")
        print("📚 Alternative Documentation:")  
        print("   http://127.0.0.1:8000/redoc")
        print("")
        print("🔧 API Endpoints:")
        print("   GET  /npcs              - List available NPCs")
        print("   POST /test-filtering    - Test NPC reactions")
        print("   POST /build-context     - Build conversation context")
        print("   POST /chat              - Chat with NPCs (requires AI)")
        print("   POST /custom-npc        - Create custom NPCs")
        print("   GET  /sample-data       - Get sample test data")
        print("")
        print("💡 Tip: Use the /docs interface to test all endpoints!")
        print("=" * 50)
        print("")
        
        uvicorn.run(
            "web_api.main:app", 
            host="127.0.0.1", 
            port=8000, 
            reload=True,  # Auto-reload on code changes
            log_level="info"
        )
        
    except ImportError:
        print("❌ Missing dependencies!")
        print("Installing required packages...")
        install_dependencies()
        print("\n🔄 Please run this script again.")
        return
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\n💡 Make sure you're in the EliteD directory when running this script.")

if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists("src/ai_integration"):
        print("❌ Error: Please run this script from the EliteD project root directory")
        print("Current directory:", os.getcwd())
        sys.exit(1)
    
    start_server()