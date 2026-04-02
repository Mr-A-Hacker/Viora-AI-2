import os
import subprocess
import shlex
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/terminal", tags=["terminal"])

BLOCKED_COMMANDS = ['rm -rf', 'dd', 'mkfs', 'shutdown', 'reboot', 'halt', 'poweroff', 'init 0', 'init 6']

class CommandRequest(BaseModel):
    command: str
    cwd: str = None

def is_safe_command(cmd: str) -> bool:
    cmd_lower = cmd.lower().strip()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return False
    return True

@router.post("/execute")
async def execute_command(request: CommandRequest):
    if not is_safe_command(request.command):
        raise HTTPException(status_code=400, detail="Command blocked for safety")
    
    try:
        cwd = request.cwd or os.getcwd()
        result = subprocess.run(
            request.command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info")
async def get_system_info():
    return {
        "cwd": os.getcwd(),
        "user": os.environ.get("USER", "unknown"),
        "home": os.environ.get("HOME", "/root"),
    }
