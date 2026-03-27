import asyncio
import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/devai", tags=["devai"])
logger = logging.getLogger(__name__)

DEVAI_SYSTEM_PROMPT = """You are Dev AI, an expert software engineering assistant. You help with:
- Writing, debugging, and explaining code in any language
- Refactoring and improving code quality
- Answering programming questions
- Explaining algorithms and data structures
- Helping with git, terminal, and development tools

Be concise, accurate, and practical. Provide code examples when helpful.
Focus on modern best practices. If you write code, prefer Python, JavaScript/TypeScript, or the language the user asks about."""

_llm = None
_llm_lock = threading.Lock()


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm
    
    with _llm_lock:
        if _llm is not None:
            return _llm
        
        from llama_cpp import Llama
        from config import CHAT_MODEL_PATH, LOCAL_DIR, CHAT_REPO_ID, CHAT_FILENAME
        
        model_path = CHAT_MODEL_PATH
        if not os.path.exists(model_path):
            logger.info("Dev AI: Model not found at %s. Downloading...", model_path)
            from huggingface_hub import hf_hub_download
            os.makedirs(LOCAL_DIR, exist_ok=True)
            model_path = hf_hub_download(repo_id=CHAT_REPO_ID, filename=CHAT_FILENAME, local_dir=LOCAL_DIR)
        
        logger.info("Dev AI: Loading model from %s", model_path)
        _llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4,
            n_threads_batch=4,
            verbose=False
        )
        logger.info("Dev AI: Model loaded")
        return _llm


class ChatRequest(BaseModel):
    message: str


class StreamRequest(BaseModel):
    message: str
    stream: bool = True


_executor = ThreadPoolExecutor(max_workers=1)


def _generate_response_sync(messages):
    llm = _get_llm()
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=2048,
        temperature=0.7,
        top_p=0.95,
        top_k=20,
    )
    return response["choices"][0]["message"]["content"]


@router.post("/chat")
async def devai_chat(req: ChatRequest):
    """Send a message to Dev AI (offline, local model) and return the response."""
    try:
        loop = asyncio.get_event_loop()
        response_text = await loop.run_in_executor(
            _executor,
            _generate_response_sync,
            [
                {"role": "system", "content": DEVAI_SYSTEM_PROMPT},
                {"role": "user", "content": req.message}
            ]
        )
        
        cleaned = re.sub(r'<\s*think\s*>.*?<\s*/\s*think\s*>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'<\s*think\s*>[\s\S]*$', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace('<think>', '').replace('</think>', '')
        
        return {"response": cleaned.strip() or "No response from Dev AI."}
    except Exception as e:
        logger.error("Dev AI error: %s", e)
        return {"response": f"Error: {str(e)}"}


@router.post("/chat/stream")
async def devai_chat_stream(req: StreamRequest):
    """Send a message to Dev AI with streaming response."""
    from fastapi.responses import StreamingResponse
    
    async def generate():
        try:
            def gen():
                llm = _get_llm()
                messages = [
                    {"role": "system", "content": DEVAI_SYSTEM_PROMPT},
                    {"role": "user", "content": req.message}
                ]
                for chunk in llm.create_chat_completion(
                    messages=messages,
                    max_tokens=2048,
                    temperature=0.7,
                    top_p=0.95,
                    top_k=20,
                    stream=True
                ):
                    content = chunk["choices"][0].get("delta", {}).get("content", "")
                    if content:
                        cleaned = re.sub(r'<\s*think\s*>.*?<\s*/\s*think\s*>', '', content, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r'<\s*think\s*>[\s\S]*$', '', cleaned, flags=re.IGNORECASE)
                        if cleaned:
                            yield cleaned
            
            loop = asyncio.get_event_loop()
            for text in await loop.run_in_executor(_executor, lambda: list(gen())):
                yield f"data: {text}\n\n"
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("Dev AI stream error: %s", e)
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/status")
async def devai_status():
    """Check if Dev AI model is loaded."""
    global _llm
    return {
        "status": "ready" if _llm is not None else "loading",
        "model": "Qwen (offline)",
        "offline": True
    }
