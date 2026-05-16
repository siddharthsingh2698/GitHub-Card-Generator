from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.genai import types
from agent import github_card_agent
import os
import uvicorn

app = FastAPI(title="GitHub Dev Card Generator API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services and Runner
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()
runner = Runner(
    app_name="github_card_generator",
    agent=github_card_agent,
    session_service=session_service,
    memory_service=memory_service,
    auto_create_session=True
)

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
    return {"status": "healthy"}

@app.get("/card/{username}")
async def get_card(username: str):
    card_path = os.path.join(CARDS_DIR, f"{username}.html")
    if os.path.exists(card_path):
        return FileResponse(card_path)
    raise HTTPException(status_code=404, detail="Card not found")

@app.post("/generate")
async def generate_card(request: CardRequest):
    username = request.username
    session_id = f"session_{username}"
    user_id = "default_user"
    
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=f"Generate a dev card for {username}")]
    )
    
    try:
        last_text = ""
        # We process events to get the final text. 
        # For a truly streaming API, we would use StreamingResponse, 
        # but the prompt asks to return the final card URL and HTML.
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            if event.content and event.author != 'user':
                for part in event.content.parts:
                    if part.text:
                        last_text += part.text
        
        card_url = f"/static/cards/{username}.html"
        card_path = os.path.join(CARDS_DIR, f"{username}.html")
        
        html_content = ""
        if os.path.exists(card_path):
            with open(card_path, "r", encoding="utf-8") as f:
                html_content = f.read()

        return {
            "status": "success",
            "message": last_text,
            "card_url": card_url,
            "html": html_content
        }
    except Exception as e:
        print(f"Error generating card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
