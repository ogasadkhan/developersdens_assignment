from pathlib import Path
import logging
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env from the parent directory (developersdens_assignment folder)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from backend.dispatch import create_dispatch

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="DevelopersDens Outbound Dispatcher")


class CallRequest(BaseModel):
    phone_number: str
    customer_name: str | None = "Customer"
    sip_trunk_id: str | None = None
    scenario: str | None = None


@app.get("/")
async def root():
    html_path = Path(__file__).resolve().parents[1] / "static" / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {"message": "UI file missing. Expected at static/index.html"}


@app.get("/call")
async def call_help():
    return {
        "message": "Use POST /call with JSON body",
        "example": {
            "phone_number": "+17869871848",
            "customer_name": "Ali",
            "scenario": "appointment",
        },
    }


@app.post("/call")
async def trigger_call(req: CallRequest):
    try:
        result = await create_dispatch(req.phone_number, req.customer_name, req.sip_trunk_id)
        return {"status": "ok", "room": result["room"], "dispatch": result["dispatch"]}
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Error in trigger_call: {error_msg}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)
