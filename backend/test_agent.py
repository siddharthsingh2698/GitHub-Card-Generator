import asyncio
from agent import run_github_agent
from dotenv import load_dotenv

load_dotenv()

async def test():
    print("Testing ADK Agent...")
    try:
        result = await run_github_agent("torvalds")
        print("\n--- AGENT RESPONSE ---")
        print(result["message"])
    except Exception as e:
        print(f"\n--- ERROR ---")
        print(str(e))

if __name__ == "__main__":
    asyncio.run(test())
