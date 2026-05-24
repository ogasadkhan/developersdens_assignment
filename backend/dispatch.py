import os
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv
from livekit import api

# Load .env from the parent directory (developersdens_assignment folder)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

async def create_dispatch(phone_number: str, customer_name: str = "Customer", sip_trunk_id: str | None = None, livekit_url: str | None = None):
    """Create an agent dispatch on LiveKit and return the room name and dispatch info.

    This function mirrors the logic in the original `create_dispatch.py` but is
    implemented here as an async helper used by the FastAPI app.
    """
    LIVEKIT_URL = livekit_url or os.getenv("LIVEKIT_URL")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
    AGENT_NAME = os.getenv("AGENT_NAME", "outbound-agent")

    if not (LIVEKIT_URL and LIVEKIT_API_KEY and LIVEKIT_API_SECRET):
        raise EnvironmentError("LIVEKIT_URL, LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set")

    lk = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )

    room_name = f"outbound-{uuid.uuid4().hex[:8]}"

    metadata = json.dumps({
        "phone_number": phone_number,
        "customer_name": customer_name,
        "sip_trunk_id": sip_trunk_id,
    })

    req = api.CreateAgentDispatchRequest(
        agent_name=AGENT_NAME,
        room=room_name,
        metadata=metadata,
    )

    try:
        dispatch = await lk.agent_dispatch.create_dispatch(req)
        # dispatch object may not be JSON serializable, return a string repr
        return {"room": room_name, "dispatch": str(dispatch)}
    finally:
        await lk.aclose()
