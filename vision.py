import logging
import os
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/vision", tags=["vision"])

ALLOWED = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/bmp"}

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED:
        raise HTTPException(400, f"Unsupported type: {file.content_type}. Allowed: PNG, JPEG, WebP, GIF, BMP")
    ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif", "image/bmp": ".bmp"}.get(file.content_type, ".bin")
    filename = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / filename
    try:
        contents = await file.read()
        with open(path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(500, f"Failed to save: {e}")
    description = describe_image(path, file.content_type)
    return {"filename": filename, "url": f"/vision/uploads/{filename}", "description": description}

@router.get("/uploads/{filename}")
async def get_upload(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(str(path))

def describe_image(path: Path, mime: str) -> dict:
    try:
        from PIL import Image, ExifTags
        img = Image.open(path)
        w, h = img.size
        fmt = img.format or "unknown"
        info = {"width": w, "height": h, "format": fmt, "mode": img.mode, "size_bytes": path.stat().st_size}
        try:
            exif = img._getexif()
            if exif:
                for tag_id, val in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag in ("DateTimeOriginal", "Make", "Model", "Software", "Orientation"):
                        info[str(tag)] = str(val)[:60]
        except Exception:
            pass
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        if max(w, h) > 1600:
            ratio = 1600 / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        thumb_path = path.with_suffix(".thumb.jpg")
        img.convert("RGB").save(thumb_path, "JPEG", quality=75)
        info["thumbnail"] = f"/vision/uploads/{thumb_path.name}"
        return info
    except ImportError:
        return {"width": 0, "height": 0, "format": mime, "error": "Pillow not available"}
    except Exception as e:
        return {"width": 0, "height": 0, "format": mime, "error": str(e)}
