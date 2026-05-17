import time
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os
import sys
import traceback

# Try to import Google ADK components, but continue if they fail
try:
    from google.adk import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
    from google.genai import types
    from agent import github_card_agent
    AGENT_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not load agent: {e}")
    traceback.print_exc()
    AGENT_AVAILABLE = False

app = FastAPI(title="GitHub Dev Card Generator API")

# Enable CORS FIRST, before anything else
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services and Runner only if agent is available
runner = None
if AGENT_AVAILABLE:
    try:
        session_service = InMemorySessionService()
        memory_service = InMemoryMemoryService()
        runner = Runner(
            app_name="github_card_generator",
            agent=github_card_agent,
            session_service=session_service,
            memory_service=memory_service,
            auto_create_session=True
        )
    except Exception as e:
        print(f"Warning: Could not initialize runner: {e}")
        traceback.print_exc()
        runner = None

# Ensure static directories exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
CARDS_DIR = os.path.join(STATIC_DIR, "cards")
os.makedirs(CARDS_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class CardRequest(BaseModel):
    username: str

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent_available": AGENT_AVAILABLE,
        "runner_initialized": runner is not None
    }

@app.get("/card/{username}")
async def get_card(username: str):
    card_path = os.path.join(CARDS_DIR, f"{username}.html")
    if os.path.exists(card_path):
        return FileResponse(card_path)
    raise HTTPException(status_code=404, detail="Card not found")

@app.post("/generate")
async def generate_card(request: CardRequest):
    username = request.username
    
    if not runner or not AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Agent service not available. Check backend logs."
        )
    
    # Use unique session per request to avoid stale conversation history
    session_id = f"session_{username}_{int(time.time())}"
    user_id = "default_user"
    
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=f"Generate a dev card for GitHub user: {username}. You must call all 4 tools in order: scrape_github, analyze_profile, generate_card_html, save_card.")]
    )
    
    try:
        last_text = ""
        html_from_tool = ""  # capture HTML directly from generate_card_html tool response

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            # Log every event for debugging
            print(f"[EVENT] author={event.author} is_final={event.is_final_response()}")

            if event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        last_text += part.text
                        # If the tool returned HTML directly, capture it
                        text = part.text.strip()
                        if text.startswith('<') and 'div' in text and len(text) > 200:
                            print(f"[EVENT] Captured HTML from text part ({len(text)} chars)")
                            html_from_tool = text
                    # Capture tool response containing HTML
                    if hasattr(part, 'function_response') and part.function_response:
                        fn_name = getattr(part.function_response, 'name', '')
                        fn_resp = getattr(part.function_response, 'response', {})
                        print(f"[EVENT] Tool response: {fn_name} -> {str(fn_resp)[:200]}")
                        if fn_name == 'generate_card_html':
                            result = fn_resp.get('result') or fn_resp.get('output') or fn_resp.get('content') or ''
                            if isinstance(result, str) and '<div' in result:
                                html_from_tool = result
                                print(f"[EVENT] Captured HTML from generate_card_html ({len(html_from_tool)} chars)")

        card_url = f"/static/cards/{username}.html"
        card_path = os.path.join(CARDS_DIR, f"{username}.html")
        
        html_content = ""
        # First try reading from saved file
        if os.path.exists(card_path):
            with open(card_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            print(f"[INFO] Loaded HTML from file ({len(html_content)} chars)")
        
        # Fallback: use HTML captured directly from tool event
        if not html_content and html_from_tool:
            print(f"[INFO] Using HTML captured from tool event (file not saved)")
            html_content = html_from_tool
            # Save it ourselves
            with open(card_path, "w", encoding="utf-8") as f:
                f.write(html_content)

        if not html_content:
            print(f"[ERROR] No HTML found. last_text={last_text[:500]}")
            raise HTTPException(status_code=500, detail="Card was not generated. Agent did not complete all steps.")

        return {
            "status": "success",
            "message": last_text,
            "card_url": card_url,
            "html": html_content
        }
    except Exception as e:
        print(f"Error generating card: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
