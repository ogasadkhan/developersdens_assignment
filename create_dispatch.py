# outbound_dispatch1.py
import os
import json
import asyncio
import uuid
from pathlib import Path
from dotenv import load_dotenv
from livekit import api

# Prefer a project-local .env (developersdens_assignment/.env). Fall back to
# environment if not present.
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))
else:
    load_dotenv()

# You can also override `LIVEKIT_URL` via env; keep the example default here
# for local testing if desired.
LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "wss://asadleapsdev-7u4ql3u4.livekit.cloud")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")

AGENT_NAME = "outbound-agent"   # must match agent_name used when starting your worker

async def main():
    lk = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )

    # choose or generate a room name (LiveKit will create it if it doesn't exist)
    room_name = f"outbound-{uuid.uuid4().hex[:8]}"

    metadata = json.dumps({
        "phone_number": "+17869871848",
        "customer_name": "Ali",
    })

    req = api.CreateAgentDispatchRequest(
        agent_name=AGENT_NAME,
        room=room_name,
        metadata=metadata,
    )

    try:
        dispatch = await lk.agent_dispatch.create_dispatch(req)
        print("✅ Dispatch created:", dispatch)
        print("Room:", room_name)
    except Exception as e:
        print("❌ Failed to create dispatch:", e)
    finally:
        # close aiohttp session
        await lk.aclose()

if __name__ == "__main__":
    asyncio.run(main())



