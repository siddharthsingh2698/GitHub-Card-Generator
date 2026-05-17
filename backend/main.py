import time
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import traceback

app = FastAPI(title="GitHub Dev Card Generator API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    try:
        # Import tool functions directly — no agent, no chaining issues
        from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card

        print(f"[INFO] Step 1: scrape_github({username})")
        github_data = await scrape_github(username)
        if "error" in github_data:
            raise HTTPException(status_code=404, detail=github_data["error"])
        print(f"[INFO] Step 1 done: {github_data.get('name')}")

        print(f"[INFO] Step 2: analyze_profile")
        analysis = await analyze_profile(github_data)
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {analysis['error']}")
        print(f"[INFO] Step 2 done: theme={analysis.get('card_theme')}")

        print(f"[INFO] Step 3: generate_card_html")
        html_content = await generate_card_html(username, github_data, analysis)
        print(f"[INFO] Step 3 done: {len(html_content)} chars")

        print(f"[INFO] Step 4: save_card")
        card_url = await save_card(username, html_content)
        print(f"[INFO] Step 4 done: saved to {card_url}")

        return {
            "status": "success",
            "card_url": card_url,
            "html": html_content,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] generate_card failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
