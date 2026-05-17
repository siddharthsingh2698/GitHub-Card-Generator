from mcp.server.fastmcp import FastMCP
import httpx
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types

load_dotenv()

# Create an MCP server
mcp = FastMCP("GitHubDevCardGenerator")

GITHUB_API_BASE = "https://api.github.com"
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

client_genai = None
if GEMINI_API_KEY:
    client_genai = genai.Client(api_key=GEMINI_API_KEY)

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetch GitHub stats for a given user."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    async with httpx.AsyncClient(headers=headers) as client:
        # User Profile
        user_resp = await client.get(f"{GITHUB_API_BASE}/users/{username}")
        if user_resp.status_code != 200:
            return {"error": f"User {username} not found"}
        user_data = user_resp.json()

        # Repos
        repos_resp = await client.get(f"{GITHUB_API_BASE}/users/{username}/repos?sort=updated&per_page=100")
        repos = repos_resp.json() if repos_resp.status_code == 200 else []

        # Process top 6 repos (sorted by stars)
        sorted_repos = sorted(repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:6]
        top_repos = []
        languages = {}
        for r in sorted_repos:
            top_repos.append({
                "name": r.get("name"),
                "stars": r.get("stargazers_count"),
                "language": r.get("language"),
                "description": r.get("description")
            })
            lang = r.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        return {
            "name": user_data.get("name") or username,
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "avatar_url": user_data.get("avatar_url"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "top_repos": top_repos,
            "languages": languages
        }

@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:
    """Analyze GitHub profile using Gemini."""
    prompt = f"""
    Analyze this GitHub profile and return a JSON object.
    Data: {json.dumps(github_data)}
    
    Required JSON structure:
    {{
        "developer_vibe": "one sentence personality based on repos/bio",
        "top_skills": ["skill1", "skill2", "skill3"],
        "fun_fact": "something clever inferred from their repos",
        "card_theme": "one of: hacker, builder, researcher, designer, open-source-hero"
    }}
    """
    
    if not client_genai:
        return {"error": "Gemini API key not configured"}

    response = client_genai.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return json.loads(response.text)

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a self-contained HTML string for the dev card."""
    theme = analysis.get("card_theme", "builder")
    themes = {
        "hacker": "background: #0d1117; color: #58a6ff; border: 1px solid #30363d;",
        "builder": "background: #f6f8fa; color: #24292f; border: 1px solid #d0d7de;",
        "researcher": "background: #ffffff; color: #1a1a1a; border: 1px solid #eaeaea; font-family: serif;",
        "designer": "background: linear-gradient(135deg, #6e8efb, #a777e3); color: white; border: none;",
        "open-source-hero": "background: #f0fff4; color: #22863a; border: 1px solid #28a745;"
    }
    style = themes.get(theme, themes["builder"])
    
    skills_html = "".join([f'<span style="padding: 2px 8px; margin: 2px; border-radius: 12px; background: rgba(0,0,0,0.1); font-size: 0.8rem;">{s}</span>' for s in analysis.get("top_skills", [])])
    
    repos_html = "".join([f'<li><b>{r["name"]}</b> ({r["stars"]}⭐)</li>' for r in github_data.get("top_repos", [])[:3]])

    html = f"""
    <div style="width: 350px; padding: 20px; border-radius: 15px; font-family: -apple-system, sans-serif; {style}">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <img src="{github_data.get('avatar_url')}" style="width: 60px; height: 60px; border-radius: 50%; margin-right: 15px;">
            <div>
                <h2 style="margin: 0;">{github_data.get('name')}</h2>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.8;">@{username}</p>
            </div>
        </div>
        <p style="font-style: italic; margin-bottom: 10px;">"{analysis.get('developer_vibe')}"</p>
        <div style="margin-bottom: 15px;">{skills_html}</div>
        <div style="display: flex; justify-content: space-around; margin-bottom: 15px; border-top: 1px solid rgba(0,0,0,0.1); padding-top: 10px;">
            <div style="text-align: center;"><b>{github_data.get('public_repos')}</b><br><small>Repos</small></div>
            <div style="text-align: center;"><b>{github_data.get('followers')}</b><br><small>Followers</small></div>
        </div>
        <div style="font-size: 0.9rem;">
            <b>Top Repos:</b>
            <ul style="margin: 5px 0; padding-left: 20px;">{repos_html}</ul>
        </div>
        <div style="margin-top: 10px; font-size: 0.75rem; text-align: right; opacity: 0.6;">
            {analysis.get('fun_fact')}
        </div>
    </div>
    """
    return html

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Save the HTML to static/cards/{username}.html."""
    # Use absolute path relative to this file so it works regardless of cwd
    base_dir = Path(__file__).parent
    path = base_dir / "static" / "cards" / f"{username}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return f"/static/cards/{username}.html"

if __name__ == "__main__":
    mcp.run()
