import httpx
import subprocess
from fastapi import APIRouter, Query

router = APIRouter(prefix="/maps", tags=["maps"])

NOMINATIM = "https://nominatim.openstreetmap.org/search"
REVERSE    = "https://nominatim.openstreetmap.org/reverse"
HEADERS    = {"User-Agent": "VioraAI/2.0 (viora-ai-project)"}


@router.get("/search")
async def search_location(q: str = Query(..., description="Place name to search")):
    """Search for a place by name — returns lat/lon + display name."""
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        resp = await client.get(NOMINATIM, params={
            "q": q, "format": "json", "limit": 5,
            "addressdetails": 1,
        })
        resp.raise_for_status()
    results = resp.json()
    return [
        {
            "display_name": r["display_name"],
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "type": r.get("type", ""),
        }
        for r in results
    ]


@router.get("/reverse")
async def reverse_geocode(lat: float, lon: float):
    """Turn coordinates into a human-readable address."""
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        resp = await client.get(REVERSE, params={
            "lat": lat, "lon": lon, "format": "json",
        })
        resp.raise_for_status()
    data = resp.json()
    return {
        "display_name": data.get("display_name", "Unknown location"),
        "address": data.get("address", {}),
    }


@router.post("/open")
async def open_organic_maps():
    """Launch Organic Maps via Flatpak."""
    subprocess.Popen(["flatpak", "run", "app.organicmaps.desktop"])
    return {"msg": "Organic Maps opened!"}


OPENCODE_PATH = "/home/admin/.opencode/bin/opencode"

@router.post("/open-dev")
async def open_dev_ai():
    """Launch OpenCode (Dev AI) via subprocess."""
    subprocess.Popen([OPENCODE_PATH])
    return {"msg": "Dev AI opened!"}
