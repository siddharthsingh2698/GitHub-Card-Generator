# GitHub Dev Card Generator

Turn any public GitHub profile into a beautiful, shareable developer card — powered by Google Gemini AI.

🔗 **Live Demo:** [git-hub-card-generator-6mzc.vercel.app](https://git-hub-card-generator-6mzc.vercel.app)

![GitHub Dev Card Generator](https://img.shields.io/badge/Built%20with-Google%20ADK-4285F4?style=for-the-badge&logo=google)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel)
![Railway](https://img.shields.io/badge/Backend-Railway-0B0D0E?style=for-the-badge&logo=railway)

---

## What it does

Enter any public GitHub username and the app:

1. Fetches the user's profile, repos, and stats from the GitHub API
2. Analyzes the profile using **Google Gemini** to determine developer personality, top skills, and a fun fact
3. Generates a themed, visually rich **dev card** with gradients, stats, and top repositories
4. Returns the card as embeddable HTML you can share anywhere

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS, deployed on **Vercel** |
| Backend | **FastAPI** (Python), deployed on **Railway** |
| AI | **Google Gemini 2.5 Flash** via Google GenAI SDK |
| Agent Framework | **Google ADK** (Agent Development Kit) |
| Tools | **MCP** (Model Context Protocol) via FastMCP |
| GitHub Data | GitHub REST API |

---

## Architecture

```
User → Vercel (static HTML)
           ↓ POST /generate
       Railway (FastAPI)
           ↓ calls in sequence
       MCP Tools:
         1. scrape_github    → GitHub API
         2. analyze_profile  → Gemini AI
         3. generate_card_html → themed HTML card
         4. save_card        → static file storage
```

The backend exposes MCP tools as plain async Python functions and calls them directly in sequence — no agent chaining required.

---

## Card Themes

Gemini assigns one of 5 themes based on the developer's profile:

- **Hacker** — deep purple gradient
- **Builder** — navy blue gradient
- **Researcher** — teal gradient
- **Designer** — magenta/pink gradient
- **Open Source Hero** — emerald green gradient

---

## Running Locally

### Prerequisites
- Python 3.12+
- A [Gemini API key](https://aistudio.google.com)

### Setup

```bash
git clone https://github.com/your-username/github-card-generator
cd github-card-generator

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start the backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Open `public/index.html` in your browser (or serve it with any static server).

---

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `GITHUB_TOKEN` | (Optional) GitHub personal access token for higher rate limits |

---

## Deployment

### Backend → Railway
1. Connect your GitHub repo to [Railway](https://railway.app)
2. Railway auto-detects the root `Dockerfile`
3. Add `GEMINI_API_KEY` in the Railway Variables tab
4. Copy your Railway public URL

### Frontend → Vercel
1. Connect your GitHub repo to [Vercel](https://vercel.com)
2. Set Output Directory to `public`
3. Update `RAILWAY_BACKEND_URL` in `public/index.html` with your Railway URL
4. Deploy

---

## Project Structure

```
github-card-generator/
├── backend/
│   ├── main.py          # FastAPI app, /generate endpoint
│   ├── mcp_server.py    # MCP tools: scrape, analyze, generate, save
│   ├── agent.py         # Google ADK agent definition
│   ├── requirements.txt
│   └── static/cards/    # Generated card HTML files
├── public/
│   └── index.html       # Frontend (deployed to Vercel)
├── Dockerfile           # Root Dockerfile for Railway
└── railway.json         # Railway deployment config
```

---

## Built At

This project was built during the **Google Build With AI — Agent Builder Camp** workshop organized by **GeeksforGeeks × Google for Developers**, focused on building personalized agents with ADK, MCP, and Memory Bank.

---

## License

MIT
