import os
import subprocess
from typing import Any
from fastapi import APIRouter
from pathlib import Path

router = APIRouter(prefix="/games", tags=["games"])

GAME_DIRECTORIES = [
    "/opt",
    "/usr/games",
    "/usr/local/games",
    "/home/admin/Games",
    "/home/admin/.local/share/applications",
]

COMMON_GAMES = {
    "warzone2100": {
        "name": "Warzone 2100",
        "executable": "/opt/warzone2100.real",
        "icon": "🎮",
        "description": "Real-time strategy game"
    },
    "chromium": {
        "name": "Chromium Browser", 
        "executable": "chromium",
        "icon": "🌐",
        "description": "Web Browser"
    },
    "firefox": {
        "name": "Firefox",
        "executable": "firefox",
        "icon": "🦊",
        "description": "Web Browser"
    },
}

def scan_directory(dir_path):
    games = []
    if not os.path.exists(dir_path):
        return games
    
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
            name = item.lower()
            if name in COMMON_GAMES:
                games.append({
                    "id": name,
                    **COMMON_GAMES[name]
                })
            elif not item.startswith('.'):
                games.append({
                    "id": item,
                    "name": item.replace('_', ' ').replace('-', ' ').title(),
                    "executable": item_path,
                    "icon": "🎮",
                    "description": "Executable"
                })
    return games

@router.get("")
async def list_games():
    all_games = []
    seen = set()
    
    for dir_path in GAME_DIRECTORIES:
        games = scan_directory(dir_path)
        for game in games:
            if game["id"] not in seen:
                seen.add(game["id"])
                all_games.append(game)
    
    if not all_games:
        return {
            "games": [
                {"id": "warzone2100", "name": "Warzone 2100", "executable": "/opt/warzone2100.real", "icon": "🎮", "description": "RTS Game"},
                {"id": "chromium", "name": "Chromium Browser", "executable": "chromium", "icon": "🌐", "description": "Web Browser"},
            ],
            "message": "No additional games found. Add games to /opt or /usr/games"
        }
    
    return {"games": all_games}

@router.post("/launch")
async def launch_game(payload: Any = None):
    game_id = payload.get("game_id")
    executable = payload.get("executable")
    
    if not executable:
        for game in COMMON_GAMES.values():
            game_exec = game.get("executable", "")
            if game_exec and (game_exec == game_id or (isinstance(game_id, str) and game_id in game_exec)):
                executable = game_exec
                break
    
    if not executable:
        return {"success": False, "error": "No executable specified"}
    
    try:
        if os.path.isabs(executable):
            subprocess.Popen([executable], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(executable, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "message": f"Launched {game_id}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
