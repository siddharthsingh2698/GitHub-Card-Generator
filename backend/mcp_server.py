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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
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

    # Vibrant gradient per theme
    gradients = {
        "hacker":           ("135deg, #0f0c29, #302b63, #24243e", "#a78bfa", "#c4b5fd"),
        "builder":          ("135deg, #1a1a2e, #16213e, #0f3460", "#60a5fa", "#93c5fd"),
        "researcher":       ("135deg, #0f2027, #203a43, #2c5364", "#34d399", "#6ee7b7"),
        "designer":         ("135deg, #4a0072, #7b2ff7, #f107a3", "#f9a8d4", "#fbcfe8"),
        "open-source-hero": ("135deg, #134e4a, #065f46, #064e3b", "#6ee7b7", "#a7f3d0"),
    }
    grad, accent, accent_light = gradients.get(theme, gradients["builder"])

    skills = analysis.get("top_skills", [])
    skills_html = "".join([
        f'<span style="display:inline-block;padding:4px 12px;margin:3px;border-radius:100px;'
        f'background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);'
        f'font-size:11px;font-weight:600;color:#fff;letter-spacing:0.03em;">{s}</span>'
        for s in skills
    ])

    top_repos = github_data.get("top_repos", [])[:3]
    repos_html = "".join([
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'padding:8px 12px;margin-bottom:6px;border-radius:10px;'
        f'background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);">'
        f'<span style="font-size:12px;font-weight:600;color:#fff;'
        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:200px;">'
        f'{r.get("name","")}</span>'
        f'<span style="font-size:11px;color:{accent_light};white-space:nowrap;margin-left:8px;">'
        f'⭐ {r.get("stars",0)}'
        f'{"  · " + r.get("language","") if r.get("language") else ""}</span>'
        f'</div>'
        for r in top_repos
    ])

    avatar   = github_data.get("avatar_url", "")
    name     = github_data.get("name", username)
    bio      = github_data.get("bio") or analysis.get("developer_vibe", "")
    repos_n  = github_data.get("public_repos", 0)
    followers= github_data.get("followers", 0)
    fun_fact = analysis.get("fun_fact", "")
    vibe     = analysis.get("developer_vibe", "")

    html = f"""<div style="width:360px;border-radius:20px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:linear-gradient({grad});box-shadow:0 25px 60px rgba(0,0,0,0.5),0 0 0 1px rgba(255,255,255,0.08);">
  <!-- Header strip -->
  <div style="height:6px;background:linear-gradient(90deg,{accent},{accent_light});"></div>

  <div style="padding:24px;">
    <!-- Avatar + name -->
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:18px;">
      <div style="position:relative;flex-shrink:0;">
        <img src="{avatar}" style="width:68px;height:68px;border-radius:50%;border:3px solid {accent};display:block;" />
        <div style="position:absolute;bottom:0;right:0;width:18px;height:18px;border-radius:50%;background:{accent};border:2px solid #1a1a2e;display:flex;align-items:center;justify-content:center;font-size:9px;">✦</div>
      </div>
      <div style="min-width:0;">
        <div style="font-size:18px;font-weight:800;color:#fff;letter-spacing:-0.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
        <div style="font-size:12px;color:{accent};font-weight:600;margin-top:2px;">@{username}</div>
        <div style="font-size:11px;color:rgba(255,255,255,0.5);margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{bio[:60] + "…" if len(bio) > 60 else bio}</div>
      </div>
    </div>

    <!-- Vibe quote -->
    <div style="background:rgba(255,255,255,0.06);border-left:3px solid {accent};border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:18px;">
      <div style="font-size:12px;color:rgba(255,255,255,0.7);font-style:italic;line-height:1.5;">"{vibe}"</div>
    </div>

    <!-- Skills -->
    <div style="margin-bottom:18px;">{skills_html}</div>

    <!-- Stats -->
    <div style="display:flex;gap:10px;margin-bottom:18px;">
      <div style="flex:1;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:12px;text-align:center;">
        <div style="font-size:22px;font-weight:800;color:{accent_light};">{repos_n}</div>
        <div style="font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-top:2px;">Repos</div>
      </div>
      <div style="flex:1;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:12px;text-align:center;">
        <div style="font-size:22px;font-weight:800;color:{accent_light};">{followers}</div>
        <div style="font-size:10px;color:rgba(255,255,255,0.5);font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-top:2px;">Followers</div>
      </div>
    </div>

    <!-- Top repos -->
    <div style="margin-bottom:16px;">
      <div style="font-size:11px;font-weight:700;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Top Repositories</div>
      {repos_html}
    </div>

    <!-- Fun fact -->
    <div style="font-size:11px;color:rgba(255,255,255,0.35);text-align:center;line-height:1.5;border-top:1px solid rgba(255,255,255,0.07);padding-top:12px;">{fun_fact}</div>
  </div>
</div>"""
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
