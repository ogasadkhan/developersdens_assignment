from __future__ import annotations
import asyncio
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    RoomInputOptions,
    get_job_context,
)
from livekit.plugins import deepgram, silero, noise_cancellation, openai
# from livekit.plugins.turn_detector.english import EnglishModel

# Load environment variables from explicit path
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbound-agent")

# Environment variables
SIP_OUTBOUND_TRUNK_ID = os.getenv("SIP_OUTBOUND_TRUNK_ID")
LIVEKIT_HOST = os.getenv("LIVEKIT_HOST")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# ------------------- SIMPLE AGENT DEFINITION -------------------

class OutboundAgent(Agent):
    def __init__(self, customer_name: str):
        instructions = f"""
You are an AI assistant from the Vehicle Processing Department.
Your goal is to speak politely and naturally with {customer_name}.
Speak as a human would—no markdown, no asterisks, no formatting.
If the user says hello, greet them back and explain briefly why you're calling.
"""
        super().__init__(instructions=instructions)
        self.participant: rtc.RemoteParticipant | None = None

    def set_participant(self, participant: rtc.RemoteParticipant):
        self.participant = participant

# ------------------- MAIN ENTRYPOINT -------------------

async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect()

    # # Extract job metadata
    # try:
    dial_info = json.loads(ctx.job.metadata)
    # except Exception:
    # dial_info = {"phone_number": "+17869871848", "customer_name": "Customer"}
    phone_number = dial_info["phone_number"]
    customer_name = dial_info.get("customer_name", "Customer")
    sip_trunk_id = dial_info.get("sip_trunk_id") or SIP_OUTBOUND_TRUNK_ID
    
    # Create AgentSession (STT + LLM + TTS)
    session = AgentSession(
        # stt=deepgram.STT(model="nova-3"),
        stt=openai.STT(model=os.getenv("OPENAI_STT_MODEL", "whisper-1"),),
        # stt = openai.STT(model="gpt-4o-transcribe"),
        # llm=google.LLM(model="gemini-2.0-flash"),
        llm=openai.LLM(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
        ),
        # tts=deepgram.TTS(model="aura-asteria-en"),
        tts=openai.TTS(model="tts-1"),
        # tts=openai.TTS(voice="ash"),
        vad=silero.VAD.load(),
        turn_detection=None,  # EnglishModel.load(DEVICE),
    )

    # Initialize agent
    agent = OutboundAgent(customer_name=customer_name)

    # Start session first — agent joins the room
    session_task = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVCTelephony(),
            ),
        )
    )

    await session_task
    logger.info("Agent session started, now dialing user...")

    # Create outbound SIP call
    try:
        logger.info(f"Creating SIP call: trunk_id={sip_trunk_id}, phone={phone_number}")
        
        # Try with phone number as-is first
        sip_address = phone_number
        
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=sip_trunk_id,
                sip_call_to=sip_address,
                participant_identity=phone_number,
                wait_until_answered=True,
            )
        )

        participant = await ctx.wait_for_participant(identity=phone_number)
        agent.set_participant(participant)
        logger.info(f"User answered and joined: {participant.identity}")

    except api.TwirpError as e:
        logger.error(
            f"SIP call failed: {e.message} "
            f"(status {e.metadata.get('sip_status_code')} {e.metadata.get('sip_status')})"
        )
        ctx.shutdown()

# ------------------- RUN WORKER -------------------

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="outbound-agent",
        )
    )