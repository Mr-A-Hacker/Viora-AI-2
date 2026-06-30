"""
Knowledge Base — document ingestion, semantic search, and RAG for Viora AI.

Capabilities:
  - Ingest files recursively from a directory (.txt, .md, .py, .json, .csv, .yaml, .html)
  - Fetch and ingest web pages (content extraction via BeautifulSoup)
  - Add raw text entries
  - TF-IDF + keyword search (zero extra dependencies beyond numpy)
  - Optional embedding-based search when sentence-transformers is available
  - Persistent on-disk storage in knowledge/knowledge_base.json
  - CLI for batch operations
"""

import json
import logging
import math
import os
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Thread
from typing import Optional

import numpy as np
import requests

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"
KNOWLEDGE_FILE = KNOWLEDGE_DIR / "knowledge_base.json"

HEADERS = {"User-Agent": "VioraAI/1.0"}

# ─── Supported file extensions for ingestion ──────────────────
TEXT_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".yaml", ".yml", ".html", ".htm", ".xml", ".log", ".cfg", ".ini", ".conf", ".rst", ".toml"}

# ─── Embedding model (lazy loaded) ───────────────────────────
_embedder = None

def _get_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embedding model loaded (384-dim)")
        return _embedder
    except ImportError:
        logger.warning("sentence-transformers not installed; falling back to TF-IDF search")
        return None
    except Exception as e:
        logger.warning("Failed to load embedding model: %s", e)
        return None


# ─── In-memory index (built on load) ─────────────────────────
class TfIdfIndex:
    """Lightweight TF-IDF index over the knowledge base entries."""

    def __init__(self):
        self.documents: list[dict] = []
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.tf_matrix: list[Counter] = []
        self.embeddings: Optional[np.ndarray] = None
        self._dirty = False

    def tokenize(self, text: str) -> list[str]:
        text = text.lower()
        return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text)

    def build(self, documents: list[dict]):
        self.documents = documents
        all_terms: list[str] = []
        self.tf_matrix = []

        for doc in documents:
            terms = self.tokenize(doc.get("title", "") + " " + doc.get("content", ""))
            all_terms.extend(terms)
            self.tf_matrix.append(Counter(terms))

        # Vocabulary
        unique = sorted(set(all_terms))
        self.vocab = {t: i for i, t in enumerate(unique)}

        # IDF
        n_docs = len(documents)
        df = Counter(all_terms)
        self.idf = {
            term: math.log((n_docs + 1) / (count + 1)) + 1
            for term, count in df.items()
        }

        # Generate embeddings if model available
        embedder = _get_embedder()
        if embedder and documents:
            texts = [f"{d.get('title','')} {d.get('content','')}"[:2048] for d in documents]
            try:
                self.embeddings = embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
                logger.info("Generated %d embeddings (dim=%d)", len(texts), self.embeddings.shape[1])
            except Exception as e:
                logger.warning("Embedding generation failed: %s", e)
                self.embeddings = None

        self._dirty = False

    def search(self, query: str, top_k: int = 10) -> list[tuple[dict, float]]:
        if not self.documents:
            return []

        query_terms = self.tokenize(query)

        # Try semantic search first
        embedder = _get_embedder()
        if embedder and self.embeddings is not None and len(self.embeddings) == len(self.documents):
            try:
                q_vec = embedder.encode([query], normalize_embeddings=True)[0]
                scores = np.dot(self.embeddings, q_vec)
                top_indices = np.argsort(scores)[-top_k:][::-1]
                results = []
                for idx in top_indices:
                    score = float(scores[idx])
                    if score > 0.1:
                        results.append((self.documents[idx], score))
                if results:
                    return results
            except Exception as e:
                logger.warning("Semantic search failed, falling back: %s", e)

        # TF-IDF fallback
        q_counts = Counter(query_terms)
        q_norm = math.sqrt(sum(c * c for c in q_counts.values()))
        if q_norm == 0:
            return []

        scored = []
        for idx, doc_tf in enumerate(self.tf_matrix):
            dot = 0.0
            doc_norm = 0.0
            for term, qc in q_counts.items():
                if term in doc_tf:
                    tf = doc_tf[term]
                    idf = self.idf.get(term, 1.0)
                    dot += qc * tf * idf * idf
            for term, tc in doc_tf.items():
                idf = self.idf.get(term, 1.0)
                doc_norm += (tc * idf) ** 2
            doc_norm = math.sqrt(doc_norm)
            if doc_norm > 0:
                sim = dot / (q_norm * doc_norm)
                if sim > 0:
                    scored.append((self.documents[idx], sim))

        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]


# ─── Global index ────────────────────────────────────────────
_index = TfIdfIndex()


# ─── Document loading / saving ──────────────────────────────

def _normalize(entry: dict) -> dict:
    """Normalize legacy field names to new schema."""
    if "content" not in entry and "snippet" in entry:
        entry["content"] = entry.pop("snippet")
    if "type" not in entry and "query" in entry:
        entry["type"] = entry.pop("query")
    entry.setdefault("content", "")
    entry.setdefault("type", "unknown")
    entry.setdefault("source", "")
    return entry


def load() -> list[dict]:
    if not KNOWLEDGE_FILE.exists():
        return []
    try:
        with open(KNOWLEDGE_FILE) as f:
            data = json.load(f)
        entries = data if isinstance(data, list) else data.get("entries", [])
        return [_normalize(e) for e in entries]
    except Exception as e:
        logger.warning("Failed to load knowledge base: %s", e)
        return []

def save(documents: list[dict]):
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    with open(KNOWLEDGE_FILE, "w") as f:
        json.dump({"entries": documents, "entry_count": len(documents), "updated_at": time.time()}, f, indent=2)

def rebuild_index():
    docs = load()
    _index.build(docs)
    logger.info("Index rebuilt: %d documents", len(docs))
    return len(docs)


# ─── Text chunking ──────────────────────────────────────────

def chunk_text(text: str, max_chars: int = 1500, overlap: int = 100) -> list[str]:
    """Split long text into overlapping chunks for better retrieval."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            # Try to break at a sentence or paragraph boundary
            break_at = text.rfind("\n\n", start + max_chars // 2, end)
            if break_at == -1:
                break_at = text.rfind(". ", start + max_chars // 2, end)
                if break_at != -1:
                    break_at += 1
            if break_at == -1:
                break_at = text.rfind(" ", start + max_chars // 2, end)
                if break_at != -1:
                    break_at += 1
            if break_at == -1:
                break_at = end
            chunks.append(text[start:break_at].strip())
            start = break_at - overlap
        else:
            chunks.append(text[start:].strip())
            break
    return [c for c in chunks if c]


# ─── File ingestion ─────────────────────────────────────────

def read_file(path: Path) -> Optional[str]:
    try:
        return path.read_text("utf-8", errors="replace")
    except Exception:
        try:
            return path.read_text("latin-1", errors="replace")
        except Exception as e:
            logger.warning("Cannot read %s: %s", path, e)
            return None

def ingest_file(path: Path, source_label: Optional[str] = None) -> list[dict]:
    """Parse a single file into one or more knowledge entries (chunked if large)."""
    text = read_file(path)
    if not text:
        return []

    rel = path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path
    label = source_label or str(rel)
    ext = path.suffix.lower()

    if ext == ".json":
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [{"title": f"{label}[{i}]", "content": json.dumps(item, indent=2)[:3000], "source": str(rel), "type": "json"} for i, item in enumerate(data[:100])]
            elif isinstance(data, dict):
                return [{"title": label, "content": json.dumps(data, indent=2)[:5000], "source": str(rel), "type": "json"}]
        except json.JSONDecodeError:
            pass

    if ext == ".csv":
        lines = text.strip().splitlines()
        if not lines:
            return []
        header = lines[0]
        entries = []
        for i, line in enumerate(lines[1:101], 1):
            if line.strip():
                entries.append({"title": f"{label} row {i}", "content": f"{header}\n{line}", "source": str(rel), "type": "csv"})
        return entries

    title = path.stem.replace("_", " ").replace("-", " ").title()
    chunks = chunk_text(text)
    return [{"title": f"{title} (part {i+1})" if len(chunks) > 1 else title, "content": chunk, "source": str(rel), "type": ext.lstrip(".") or "text"} for i, chunk in enumerate(chunks)]


def ingest_directory(dir_path: str, recursive: bool = True) -> dict:
    """Recursively ingest all supported text files in a directory."""
    base = Path(dir_path)
    if not base.is_dir():
        return {"status": "error", "message": f"Not a directory: {dir_path}"}

    existing = load()
    seen_sources = {e.get("source", "") for e in existing}

    files = list(base.rglob("*") if recursive else base.glob("*"))
    text_files = [f for f in files if f.is_file() and f.suffix.lower() in TEXT_EXTENSIONS]

    total_added = 0
    total_skipped = 0
    new_entries = []

    for f in text_files:
        rel = str(f.relative_to(Path.cwd())) if f.is_relative_to(Path.cwd()) else str(f)
        if rel in seen_sources:
            total_skipped += 1
            continue
        entries = ingest_file(f)
        if entries:
            new_entries.extend(entries)
            total_added += len(entries)
            seen_sources.add(rel)

    if new_entries:
        existing.extend(new_entries)
        save(existing)
        rebuild_index()

    return {"status": "ok", "added": total_added, "skipped": total_skipped, "total": len(existing)}


def ingest_text(text: str, title: str = "Untitled", source: str = "manual", content_type: str = "text") -> dict:
    """Add a raw text entry (chunked if long)."""
    existing = load()
    chunks = chunk_text(text)
    entries = [{"title": f"{title} (part {i+1})" if len(chunks) > 1 else title, "content": chunk, "source": f"{source}#p{i+1}" if len(chunks) > 1 else source, "type": content_type} for i, chunk in enumerate(chunks)]

    seen_sources = {e.get("source", "") for e in existing}
    new = [e for e in entries if e["source"] not in seen_sources]
    if not new:
        return {"status": "ok", "added": 0, "message": "Already exists"}

    existing.extend(new)
    save(existing)
    rebuild_index()
    return {"status": "ok", "added": len(new), "total": len(existing)}


# ─── Web page ingestion ─────────────────────────────────────

def fetch_and_ingest(url: str) -> dict:
    """Fetch a web page, extract text, and add to knowledge base."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        clean = "\n".join(lines)
    except Exception as e:
        return {"status": "error", "message": f"Parse failed: {e}"}

    return ingest_text(clean, title=title, source=url, content_type="web")


# ─── Search ─────────────────────────────────────────────────

def search(query: str, top_k: int = 10) -> list[dict]:
    """Search knowledge base, return entries with relevance scores."""
    results = _index.search(query, top_k=top_k)
    return [{"title": doc.get("title", ""), "content": doc.get("content", ""), "source": doc.get("source", ""), "type": doc.get("type", ""), "score": round(score, 4)} for doc, score in results]


def format_for_prompt(entries: list[dict], max_tokens: int = 3000) -> str:
    """Format search results into a prompt-friendly string, respecting token budget."""
    parts = ["Here is relevant information from the knowledge base:"]
    char_budget = max_tokens * 4
    used = 0
    for e in entries:
        snippet = f"\n• {e['title']}: {e['content'][:600]}"
        if e.get("source"):
            snippet += f" ({e['source']})"
        if used + len(snippet) > char_budget:
            break
        parts.append(snippet)
        used += len(snippet)
    return "\n".join(parts)


def search_and_format(query: str, top_k: int = 5, max_tokens: int = 3000) -> str:
    """Convenience: search → format results for prompt injection."""
    entries = search(query, top_k=top_k)
    if entries:
        return format_for_prompt(entries, max_tokens=max_tokens)
    return ""


# ─── Stats ──────────────────────────────────────────────────

def stats() -> dict:
    entries = load()
    total_chars = sum(len(e.get("content", "")) for e in entries)
    types = Counter(e.get("type", "unknown") for e in entries)
    return {
        "total_entries": len(entries),
        "total_chars": total_chars,
        "type_breakdown": dict(types),
        "file_size_mb": round(KNOWLEDGE_FILE.stat().st_size / (1024 * 1024), 2) if KNOWLEDGE_FILE.exists() else 0,
        "embedder_available": _get_embedder() is not None,
        "index_built": len(_index.documents),
    }


# ─── Delete ─────────────────────────────────────────────────

def delete_by_source(source: str) -> int:
    """Delete entries whose source exactly matches or starts with the given source (to handle chunked entries: source#p1, source#p2, ...)."""
    entries = load()
    before = len(entries)
    entries = [e for e in entries if e.get("source", "") != source and not e.get("source", "").startswith(source + "#")]
    removed = before - len(entries)
    if removed:
        save(entries)
        rebuild_index()
    return removed


def delete_all() -> int:
    entries = load()
    count = len(entries)
    save([])
    _index = TfIdfIndex()
    return count


# ─── Legacy update support (HN, Reddit, YouTube, etc.) ──────

HN_NEW = "https://hacker-news.firebaseio.com/v0/newstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"

REDDITS = ["news", "worldnews", "technology", "anime", "gaming", "science", "entertainment", "movies", "music", "sports", "todayilearned", "explainlikeimfive", "space", "books", "television", "food", "history", "philosophy", "futurology"]

TARGET_COUNT = 1000
_updating = False
_progress = 0


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
            return {"title": title, "content": text, "source": d.get("url") or f"https://news.ycombinator.com/item?id={item_id}", "type": "hackernews"}
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
            entries.append({"title": title, "content": selftext, "source": d.get("url") or f"https://reddit.com/r/{subreddit}", "type": "reddit"})
        return entries
    except Exception as e:
        logger.warning("Reddit r/%s failed: %s", subreddit, e)
        return []


YOUTUBE_QUERIES = ["site:youtube.com trending", "site:youtube.com news today", "site:youtube.com technology", "site:youtube.com anime", "site:youtube.com science", "site:youtube.com gaming", "site:youtube.com entertainment", "site:youtube.com music", "site:youtube.com sports"]


def _youtube_query(d, query: str) -> list[dict]:
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
                results.append({"title": title, "content": snippet, "source": href, "type": "youtube"})
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


LINKEDIN_QUERIES = ["site:linkedin.com/pulse", "site:linkedin.com/news", "site:linkedin.com/company"]


def _linkedin_query(d, query: str) -> list[dict]:
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
                results.append({"title": title, "content": snippet, "source": href, "type": "linkedin"})
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


WIKI_BATCH = "https://en.wikipedia.org/w/api.php"


def _fetch_wiki_batch(count: int = 50) -> list[dict]:
    params = {"action": "query", "generator": "random", "grnnamespace": 0, "grnlimit": count, "prop": "extracts", "exintro": True, "explaintext": True, "format": "json"}
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
                entries.append({"title": title, "content": extract[:800], "source": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}", "type": "wikipedia"})
        return entries
    except Exception as e:
        logger.warning("Wiki batch failed: %s", e)
        return []


def update_knowledge() -> dict:
    """Legacy online knowledge fetch (HN, Reddit, YouTube, LinkedIn, Wikipedia)."""
    global _updating, _progress
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    _updating = True
    _progress = 0

    existing = load()
    seen_sources = {e.get("source", "") for e in existing}

    def add(entries):
        added = 0
        for e in entries:
            key = e.get("source", "") or e.get("title", "")
            if key and key not in seen_sources:
                seen_sources.add(key)
                existing.append(e)
                added += 1
        return added

    added_total = 0

    logger.info("Fetching Hacker News...")
    hn_entries, _ = _fetch_hn()
    added_total += add(hn_entries)
    _progress = len(existing)

    logger.info("Fetching Reddit...")
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_fetch_reddit, sub): sub for sub in REDDITS}
        for f in as_completed(futures):
            if len(existing) >= TARGET_COUNT:
                break
            added_total += add(f.result())
            _progress = len(existing)

    logger.info("Fetching YouTube...")
    added_total += add(_fetch_youtube())
    _progress = len(existing)

    logger.info("Fetching LinkedIn...")
    added_total += add(_fetch_linkedin())
    _progress = len(existing)

    if len(existing) < TARGET_COUNT:
        logger.info("Fetching Wikipedia...")
        remaining = TARGET_COUNT - len(existing)
        for _ in range((remaining // 50) + 2):
            added_total += add(_fetch_wiki_batch())
            _progress = len(existing)
            if len(existing) >= TARGET_COUNT:
                break

    if len(existing) > TARGET_COUNT:
        existing[:] = existing[-TARGET_COUNT:]

    save(existing)
    rebuild_index()
    _updating = False
    logger.info("Knowledge update complete: added=%d total=%d", added_total, len(existing))
    return {"status": "completed", "added": added_total, "total": len(existing)}


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


def get_knowledge() -> dict:
    entries = load()
    return {"updating": _updating, "progress": _progress, "entries": entries[-50:], "entry_count": len(entries), "updated_at": KNOWLEDGE_FILE.stat().st_mtime if KNOWLEDGE_FILE.exists() else None}


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
    return {"status": "up_to_date", "current_hn_id": current_id, "stored_hn_id": stored_id}


# ─── Legacy compatibility aliases ──────────────────────────
search_knowledge = search
format_knowledge_for_prompt = format_for_prompt


# ─── CLI ─────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Viora AI Knowledge Base Manager")
    parser.add_argument("--ingest", type=str, help="Ingest files from a directory")
    parser.add_argument("--fetch", type=str, help="Fetch and ingest a web page URL")
    parser.add_argument("--add", type=str, help="Add raw text")
    parser.add_argument("--title", type=str, default="Untitled", help="Title for --add")
    parser.add_argument("--search", type=str, help="Search the knowledge base")
    parser.add_argument("--top-k", type=int, default=5, help="Number of search results")
    parser.add_argument("--stats", action="store_true", help="Show knowledge base stats")
    parser.add_argument("--update-legacy", action="store_true", help="Run legacy online update (HN, Reddit, etc.)")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild search index")
    parser.add_argument("--delete-source", type=str, help="Delete entries by source")
    parser.add_argument("--delete-all", action="store_true", help="Delete all entries")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.rebuild:
        n = rebuild_index()
        print(f"Index rebuilt: {n} documents")

    if args.ingest:
        result = ingest_directory(args.ingest)
        print(json.dumps(result, indent=2))

    if args.fetch:
        result = fetch_and_ingest(args.fetch)
        print(json.dumps(result, indent=2))

    if args.add:
        result = ingest_text(args.add, title=args.title)
        print(json.dumps(result, indent=2))

    if args.search:
        results = search(args.search, top_k=args.top_k)
        print(f"Found {len(results)} results for: {args.search}")
        for r in results:
            print(f"  [{r['score']:.3f}] {r['title']} ({r['source']})")
            print(f"       {r['content'][:120]}...")

    if args.stats:
        s = stats()
        print(f"Total entries: {s['total_entries']}")
        print(f"Total chars: {s['total_chars']:,}")
        print(f"File size: {s['file_size_mb']} MB")
        print(f"Embedder: {'available' if s['embedder_available'] else 'not available'}")
        print(f"By type: {s['type_breakdown']}")

    if args.update_legacy:
        result = update_knowledge()
        print(json.dumps(result, indent=2))

    if args.delete_source:
        n = delete_by_source(args.delete_source)
        print(f"Deleted {n} entries with source: {args.delete_source}")

    if args.delete_all:
        n = delete_all()
        print(f"Deleted all {n} entries")


if __name__ == "__main__":
    main()
