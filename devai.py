import re
import subprocess
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/devai", tags=["devai"])

OPENCODE_PATH = "/home/admin/.opencode/bin/opencode"


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def devai_chat(req: ChatRequest):
    """Send a message to OpenCode and return the response."""
    try:
        result = subprocess.run(
            [OPENCODE_PATH, "run", req.message],
            capture_output=True,
            text=True,
            timeout=120,
        )
        raw = result.stdout + result.stderr
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        output = ansi_escape.sub('', raw).strip()
        return {"response": output or "No response from Dev AI."}
    except subprocess.TimeoutExpired:
        return {"response": "Dev AI took too long to respond."}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
