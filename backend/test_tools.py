import asyncio
import json
import os
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card

async def test_end_to_end():
    username = "torvalds"
    print(f"--- Starting E2E Test for {username} ---")
    
    # 1. Scrape
    print("[1/4] Calling scrape_github...")
    github_data = await scrape_github(username)
    if "error" in github_data:
        print(f"FAILED at scrape_github: {github_data['error']}")
        return

    # 2. Analyze
    print("[2/4] Calling analyze_profile...")
    try:
        analysis = await analyze_profile(github_data)
    except Exception as e:
        print(f"FAILED at analyze_profile: {str(e)}")
        return

    # 3. Generate HTML
    print("[3/4] Calling generate_card_html...")
    try:
        html = await generate_card_html(username, github_data, analysis)
    except Exception as e:
        print(f"FAILED at generate_card_html: {str(e)}")
        return

    # 4. Save
    print("[4/4] Calling save_card...")
    try:
        path = await save_card(username, html)
    except Exception as e:
        print(f"FAILED at save_card: {str(e)}")
        return

    print("\n--- TEST SUCCESSFUL ---")
    print(f"Username: {username}")
    print(f"Card Theme: {analysis.get('card_theme')}")
    print(f"Developer Vibe: {analysis.get('developer_vibe')}")
    print(f"Relative Path: {path}")
    print(f"Full Path: {os.path.abspath(f'static/cards/{username}.html')}")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
