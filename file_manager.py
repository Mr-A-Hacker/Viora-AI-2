import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/files", tags=["files"])

BASE_DIR = os.environ.get("FILE_MANAGER_ROOT", "/home/admin")

class FileItem(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    modified: float

@router.get("/list")
async def list_directory(path: str = ""):
    target = os.path.join(BASE_DIR, path) if path else BASE_DIR
    
    if not os.path.exists(target):
        raise HTTPException(status_code=404, detail="Path not found")
    
    if not os.path.isdir(target):
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    try:
        items = []
        for item in os.listdir(target):
            item_path = os.path.join(target, item)
            try:
                stat = os.stat(item_path)
                items.append(FileItem(
                    name=item,
                    path=item,
                    is_dir=os.path.isdir(item_path),
                    size=stat.st_size if not os.path.isdir(item_path) else 0,
                    modified=stat.st_mtime
                ))
            except:
                pass
        
        items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
        return {"path": path, "items": items, "base": BASE_DIR}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/read")
async def read_file(path: str):
    target = os.path.join(BASE_DIR, path)
    
    if not os.path.exists(target):
        raise HTTPException(status_code=404, detail="File not found")
    
    if os.path.isdir(target):
        raise HTTPException(status_code=400, detail="Cannot read directory")
    
    try:
        with open(target, 'r') as f:
            content = f.read(10000)
        return {"content": content, "size": len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_file(path: str, is_dir: bool = False):
    target = os.path.join(BASE_DIR, path)
    
    try:
        if is_dir:
            os.makedirs(target, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'w') as f:
                f.write('')
        return {"status": "created", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
async def delete_file(path: str):
    target = os.path.join(BASE_DIR, path)
    
    if not os.path.exists(target):
        raise HTTPException(status_code=404, detail="Path not found")
    
    if target == BASE_DIR:
        raise HTTPException(status_code=400, detail="Cannot delete base directory")
    
    try:
        if os.path.isdir(target):
            shutil.rmtree(target)
        else:
            os.remove(target)
        return {"status": "deleted", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rename")
async def rename_file(old_path: str, new_name: str):
    old_target = os.path.join(BASE_DIR, old_path)
    new_target = os.path.join(os.path.dirname(old_target), new_name)
    
    if not os.path.exists(old_target):
        raise HTTPException(status_code=404, detail="Path not found")
    
    try:
        os.rename(old_target, new_target)
        return {"status": "renamed", "old": old_path, "new": new_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
