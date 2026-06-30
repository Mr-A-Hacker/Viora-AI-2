import os
import mimetypes
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/videos", tags=["videos"])

VIDEO_DIR = os.path.expanduser("~/Downloads")
VIDEO_EXTS = (".mp4", ".webm", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".m4v", ".3gp", ".mpg", ".mpeg")

def is_video(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in VIDEO_EXTS

@router.get("/list")
async def list_videos():
    if not os.path.isdir(VIDEO_DIR):
        return {"videos": []}
    videos = []
    for f in sorted(os.listdir(VIDEO_DIR), key=str.lower):
        if is_video(f):
            fpath = os.path.join(VIDEO_DIR, f)
            try:
                stat = os.stat(fpath)
                size_mb = stat.st_size / (1024 * 1024)
                videos.append({
                    "name": f,
                    "size_mb": round(size_mb, 1),
                    "modified": stat.st_mtime,
                })
            except OSError:
                continue
    return {"videos": videos, "path": VIDEO_DIR}

@router.get("/stream/{filename:path}")
async def stream_video(filename: str):
    filepath = os.path.normpath(os.path.join(VIDEO_DIR, filename))
    if not filepath.startswith(VIDEO_DIR):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type:
        mime_type = "video/mp4"
    return FileResponse(filepath, media_type=mime_type)
