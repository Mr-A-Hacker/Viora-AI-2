import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread

import requests

KNOWLEDGE_DIR = "knowledge"
KNOWLEDGE_FILE = os.path.join(KNOWLEDGE_DIR, "knowledge_base.json")

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "VioraAI/1.0"}

HN_NEW = "https://hacker-news.firebaseio.com/v0/newstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"

REDDITS = [
    "news", "worldnews", "technology", "anime", "gaming",
    "science", "entertainment", "movies", "music", "sports",
    "todayilearned", "explainlikeimfive", "space", "books",
    "television", "food", "history", "philosophy", "futurology",
]

TARGET_COUNT = 1000

_updating = False
_progress = 0


# ─── Hacker News ──────────────────────────────────────────────

def _fetch_hn() -> tuple[list[dict], int]:
    latest_id = 0
    try:
        resp = requests.get(HN_NEW, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return [], 0
        all_ids = resp.json()
        if all_ids:
            latest_id = max(all_ids)
    except Exception as e:
        logger.warning("HN IDs failed: %s", e)
        return [], 0

    entries = []
    target = min(300, len(all_ids))

    def fetch_one(item_id):
        try:
            r = requests.get(HN_ITEM.format(id=item_id), headers=HEADERS, timeout=10)
            if r.status_code != 200:
                return None
            d = r.json()
            title = (d.get("title") or "").strip()
            if not title:
                return None
            text = (d.get("text") or d.get("url") or "")[:500]
            return {"title": title, "snippet": text, "source": d.get("url") or f"https://news.ycombinator.com/item?id={item_id}", "query": "hackernews"}
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(fetch_one, i): i for i in all_ids[:target]}
        for f in as_completed(futures):
            entry = f.result()
            if entry:
                entries.append(entry)
                if len(entries) >= 200:
                    break

    return entries, latest_id


# ─── Reddit ──────────────────────────────────────────────────

def _fetch_reddit(subreddit: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=15"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        children = data.get("data", {}).get("children", [])
        entries = []
        for child in children:
            d = child.get("data", {})
            title = (d.get("title") or "").strip()
            if not title:
                continue
            selftext = (d.get("selftext") or d.get("url") or "")[:500]
            entries.append({
                "title": title,
                "snippet": selftext,
                "source": d.get("url") or f"https://reddit.com/r/{subreddit}",
                "query": f"reddit/{subreddit}",
            })
        return entries
    except Exception as e:
        logger.warning("Reddit r/%s failed: %s", subreddit, e)
        return []


# ─── YouTube ──────────────────────────────────────────────

YOUTUBE_QUERIES = [
    "site:youtube.com trending",
    "site:youtube.com news today",
    "site:youtube.com technology",
    "site:youtube.com anime",
    "site:youtube.com science",
    "site:youtube.com gaming",
    "site:youtube.com entertainment",
    "site:youtube.com music",
    "site:youtube.com sports",
]

def _youtube_query(d, query: str) -> list[dict]:
    """Run a single DDGS query for YouTube content with a short timeout."""
    results = []
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(lambda: list(d.text(query, max_results=10)))
            for r in fut.result(timeout=12):
                title = (r.get("title") or "").strip()
                href = r.get("href") or ""
                if not title or not href:
                    continue
                snippet = (r.get("body") or "")[:500]
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "source": href,
                    "query": "youtube",
                })
    except Exception as e:
        logger.warning("YouTube query %s failed: %s", query, e)
    return results


def _fetch_youtube() -> list[dict]:
    entries = []
    try:
        from ddgs import DDGS
        with DDGS() as d:
            for query in YOUTUBE_QUERIES:
                entries.extend(_youtube_query(d, query))
    except ImportError:
        logger.warning("ddgs not installed, skipping YouTube")
    except Exception as e:
        logger.warning("YouTube fetch failed: %s", e)

    logger.info("YouTube done: %d entries", len(entries))
    return entries


# ─── LinkedIn ─────────────────────────────────────────────

LINKEDIN_QUERIES = [
    "site:linkedin.com/pulse",
    "site:linkedin.com/news",
    "site:linkedin.com/company",
]

def _linkedin_query(d, query: str) -> list[dict]:
    """Run a single DDGS query for LinkedIn content with a short timeout."""
    results = []
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(lambda: list(d.text(query, max_results=10)))
            for r in fut.result(timeout=12):
                title = (r.get("title") or "").strip()
                href = r.get("href") or ""
                if not title or not href:
                    continue
                snippet = (r.get("body") or "")[:500]
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "source": href,
                    "query": "linkedin",
                })
    except Exception as e:
        logger.warning("LinkedIn query %s failed: %s", query, e)
    return results


def _fetch_linkedin() -> list[dict]:
    entries = []
    try:
        from ddgs import DDGS
        with DDGS() as d:
            for query in LINKEDIN_QUERIES:
                entries.extend(_linkedin_query(d, query))
    except ImportError:
        logger.warning("ddgs not installed, skipping LinkedIn")
    except Exception as e:
        logger.warning("LinkedIn fetch failed: %s", e)

    return entries


# ─── Wikipedia ───────────────────────────────────────────────

WIKI_BATCH = "https://en.wikipedia.org/w/api.php"


def _fetch_wiki_batch(count: int = 50) -> list[dict]:
    params = {
        "action": "query",
        "generator": "random",
        "grnnamespace": 0,
        "grnlimit": count,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "format": "json",
    }
    try:
        resp = requests.get(WIKI_BATCH, params=params, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return []
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        entries = []
        for pid, page in pages.items():
            title = page.get("title", "")
            extract = page.get("extract", "")
            if title and extract:
                entries.append({
                    "title": title,
                    "snippet": extract[:500],
                    "source": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    "query": "wikipedia",
                })
        return entries
    except Exception as e:
        logger.warning("Wiki batch failed: %s", e)
        return []


# ─── Main ─────────────────────────────────────────────────────

def update_knowledge() -> dict:
    global _updating, _progress
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    _updating = True
    _progress = 0

    seen_ids = set()
    all_entries = []

    # Load existing entries and seed dedup set so the same source
    # is never added twice across consecutive updates
    if os.path.exists(KNOWLEDGE_FILE):
        try:
            with open(KNOWLEDGE_FILE) as f:
                existing = json.load(f)
            for e in existing.get("entries", []):
                key = e.get("source", "") or e.get("title", "")
                if key:
                    seen_ids.add(key)
                all_entries.append(e)
            logger.info("Loaded %d existing entries + %d seed IDs",
                        len(all_entries), len(seen_ids))
        except Exception as e:
            logger.warning("Could not read existing knowledge: %s", e)

    def add(entries):
        for e in entries:
            key = e.get("source", "") or e.get("title", "")
            if key and key not in seen_ids:
                seen_ids.add(key)
                all_entries.append(e)

    # Phase 1: Hacker News (fast, current tech/news)
    logger.info("Fetching Hacker News...")
    hn_entries, latest_hn_id = _fetch_hn()
    add(hn_entries)
    _progress = len(all_entries)
    logger.info("HN done: %d entries", len(all_entries))

    # Phase 2: Reddit (current events, anime, culture, etc.) — parallel
    logger.info("Fetching Reddit...")
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_fetch_reddit, sub): sub for sub in REDDITS}
        for f in as_completed(futures):
            if len(all_entries) >= TARGET_COUNT:
                break
            add(f.result())
            _progress = len(all_entries)
    logger.info("Reddit done: %d entries", len(all_entries))

    # Phase 3: YouTube (channel RSS feeds — latest videos from news/tech/anime)
    logger.info("Fetching YouTube...")
    add(_fetch_youtube())
    _progress = len(all_entries)
    logger.info("YouTube done: %d entries", len(all_entries))

    # Phase 4: LinkedIn (DDGS search for pulse articles, companies, news)
    logger.info("Fetching LinkedIn...")
    add(_fetch_linkedin())
    _progress = len(all_entries)
    logger.info("LinkedIn done: %d entries", len(all_entries))

    # Phase 5: Wikipedia random batches (fill remaining up to target)
    if len(all_entries) < TARGET_COUNT:
        logger.info("Fetching Wikipedia to reach %d...", TARGET_COUNT)
        remaining = TARGET_COUNT - len(all_entries)
        wiki_batches = (remaining // 50) + 2
        for i in range(wiki_batches):
            add(_fetch_wiki_batch())
            _progress = len(all_entries)
            if len(all_entries) >= TARGET_COUNT:
                break
        logger.info("Wikipedia done: %d entries", len(all_entries))

    # Trim to target count — keep newest entries (appended last)
    if len(all_entries) > TARGET_COUNT:
        all_entries[:] = all_entries[-TARGET_COUNT:]

    data = {
        "updating": False,
        "progress": len(all_entries),
        "updated_at": time.time(),
        "latest_hn_id": latest_hn_id,
        "entries": all_entries,
        "entry_count": len(all_entries),
    }

    with open(KNOWLEDGE_FILE, "w") as f:
        json.dump(data, f, indent=2)

    _updating = False
    logger.info("Knowledge update complete: %d entries", len(all_entries))
    return {"status": "completed", "entries": len(all_entries)}


# ─── Helpers ─────────────────────────────────────────────────

def get_knowledge() -> dict:
    if not os.path.exists(KNOWLEDGE_FILE):
        return {"updating": _updating, "progress": _progress, "entries": [], "entry_count": 0, "updated_at": None}
    with open(KNOWLEDGE_FILE) as f:
        data = json.load(f)
    data["updating"] = _updating
    data["progress"] = _progress
    return data


def check_updates() -> dict:
    stored = get_knowledge()
    stored_id = stored.get("latest_hn_id", 0)

    try:
        resp = requests.get(HN_NEW, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return {"status": "unknown", "error": "HN API unreachable"}
        current_ids = resp.json()
        current_id = max(current_ids) if current_ids else 0
    except Exception as e:
        return {"status": "unknown", "error": str(e)}

    if current_id > stored_id:
        new_count = sum(1 for i in current_ids if i > stored_id)
        return {"status": "update_available", "new_entries": min(new_count, 500), "current_hn_id": current_id, "stored_hn_id": stored_id}
    else:
        return {"status": "up_to_date", "current_hn_id": current_id, "stored_hn_id": stored_id}


def search_knowledge(query: str, max_results: int = 5) -> list[dict]:
    if not os.path.exists(KNOWLEDGE_FILE):
        return []
    with open(KNOWLEDGE_FILE) as f:
        data = json.load(f)

    entries = data.get("entries", [])
    if not entries:
        topics = data.get("topics", {})
        if topics:
            entries = [{"title": t, "snippet": s[:500], "source": ""} for t, s in topics.items()]
    if not entries:
        return []

    query_lower = query.lower()
    query_words = set(re.findall(r"\w+", query_lower))
    scored = []
    for entry in entries:
        combined = ((entry.get("title") or "") + " " + (entry.get("snippet") or "")).lower()
        words = set(re.findall(r"\w+", combined))
        overlap = len(query_words & words)
        if overlap > 0:
            scored.append((overlap, entry))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:max_results]]


def format_knowledge_for_prompt(entries: list[dict]) -> str:
    parts = []
    for e in entries:
        title = e.get("title", "")
        snippet = e.get("snippet", "")
        source = e.get("source", "")
        parts.append(f"• {title}: {snippet}" + (f" ({source})" if source else ""))
    return "\n".join(parts)


def update_knowledge_async(callback=None):
    def _run():
        try:
            result = update_knowledge()
            if callback:
                callback(result)
        except Exception as e:
            global _updating
            _updating = False
            logger.exception("Knowledge update failed: %s", e)
    Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = update_knowledge()
    print(json.dumps(result, indent=2))
