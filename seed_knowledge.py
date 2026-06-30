"""
Seed the knowledge base with comprehensive content:
  - Wikipedia articles across politics, languages, grammar, history, science, tech, arts
  - Current Hacker News + Reddit stories
  - Web search results for current events
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from knowledge import ingest_text, ingest_directory, delete_by_source, rebuild_index, stats

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "VioraAI/1.0"}
WIKI_API = "https://en.wikipedia.org/w/api.php"


# ─── Wikipedia topic search ─────────────────────────────────

WIKI_TOPICS = {
    # Politics
    "Politics": [
        "Politics", "Democracy", "Republic", "Monarchy", "Authoritarianism",
        "Political_party", "Election", "Voting", "Constitution", "Separation_of_powers",
        "Foreign_policy", "Diplomacy", "United_Nations", "European_Union", "NATO",
        "G20", "World_Trade_Organization", "International_Monetary_Fund",
        "United_States_government", "UK_government", "China_government", "Russia_government",
        "India_government", "Germany_government", "France_government", "Japan_government",
        "Political_ideology", "Conservatism", "Liberalism", "Socialism", "Communism",
        "Fascism", "Nationalism", "Anarchism", "Libertarianism", "Environmentalism",
    ],
    # Languages & Grammar
    "Languages": [
        "Language", "Grammar", "Linguistics", "Phonetics", "Phonology", "Morphology",
        "Syntax", "Semantics", "Pragmatics", "Historical_linguistics",
        "Indo-European_languages", "Germanic_languages", "Romance_languages",
        "Slavic_languages", "Sino-Tibetan_languages", "Austronesian_languages",
        "English_language", "Spanish_language", "Mandarin_Chinese", "Hindi",
        "Arabic", "Russian", "French", "German", "Japanese_language", "Korean_language",
        "Portuguese_language", "Italian_language", "Language_family",
        "Writing_system", "Alphabet", "Chinese_characters", "Cyrillic_script",
        "Arabic_script", "Sign_language", "Constructed_language", "Esperanto",
        "Translation", "Bilingualism", "Language_acquisition", "Speech",
        "Dialect", "Sociolinguistics", "Pidgin", "Creole_language",
        "Grammar#Parts_of_speech", "Verb", "Noun", "Adjective", "Adverb",
        "Preposition", "Conjunction", "Pronoun", "Tense", "Grammatical_aspect",
        "Grammatical_mood", "Grammatical_voice", "Grammatical_case", "Grammatical_number",
        "Grammatical_gender", "Sentence_(linguistics)", "Clause", "Phrase",
        "Subject_(grammar)", "Object_(grammar)", "Predicate_(grammar)",
    ],
    # History
    "History": [
        "History", "Ancient_history", "Middle_Ages", "Renaissance", "Industrial_Revolution",
        "World_War_I", "World_War_II", "Cold_War", "French_Revolution", "Russian_Revolution",
        "American_Revolution", "Chinese_Revolution", "Space_Race",
        "History_of_Europe", "History_of_Asia", "History_of_Africa",
        "History_of_North_America", "History_of_South_America",
        "Ancient_Egypt", "Ancient_Greece", "Roman_Empire", "Mongol_Empire",
        "British_Empire", "Ottoman_Empire", "Byzantine_Empire",
    ],
    # Science & Technology
    "Science": [
        "Science", "Physics", "Chemistry", "Biology", "Astronomy", "Geology",
        "Mathematics", "Computer_science", "Artificial_intelligence",
        "Machine_learning", "Quantum_mechanics", "Relativity", "Evolution",
        "Genetics", "Cell_biology", "Ecology", "Climate_change",
        "Solar_System", "Star", "Galaxy", "Black_hole", "DNA",
        "Internet", "World_Wide_Web", "Programming_language", "Operating_system",
        "Database", "Cryptography", "Robotics", "Nanotechnology",
        "Renewable_energy", "Nuclear_power", "Space_exploration",
    ],
    # Geography
    "Geography": [
        "Geography", "Continent", "Country", "Capital_city", "Mountain",
        "River", "Ocean", "Desert", "Climate", "Population",
        "United_States", "China", "India", "Russia", "Brazil",
        "United_Kingdom", "Germany", "France", "Japan", "Australia",
        "Canada", "Mexico", "Indonesia", "Nigeria", "Egypt",
        "European_Union", "Africa", "Asia", "Europe", "South_America",
        "North_America", "Antarctica", "Arctic", "Pacific_Ocean",
    ],
    # Arts & Culture
    "Arts": [
        "Art", "Music", "Literature", "Film", "Theatre", "Dance",
        "Painting", "Sculpture", "Architecture", "Photography",
        "Classical_music", "Jazz", "Rock_music", "Pop_music", "Hip_hop_music",
        "Novel", "Poetry", "Drama", "Comedy", "Tragedy",
        "Cinema_of_the_United_States", "Bollywood", "Anime", "Video_game",
    ],
    # Economics & Business
    "Economics": [
        "Economics", "Capitalism", "Market_economy", "Supply_and_demand",
        "Inflation", "Unemployment", "Gross_domestic_product",
        "Stock_market", "Bank", "Central_bank", "Cryptocurrency",
        "Trade", "Globalization", "Tax", "Budget", "Investment",
        "Corporation", "Entrepreneurship", "Marketing", "E-commerce",
    ],
    # Philosophy & Religion
    "Philosophy": [
        "Philosophy", "Ethics", "Logic", "Metaphysics", "Epistemology",
        "Aesthetics", "Consciousness", "Free_will", "Determinism",
        "Religion", "Christianity", "Islam", "Hinduism", "Buddhism",
        "Judaism", "Atheism", "Secularism", "Mythology",
    ],
}


def wiki_search_titles(query: str, limit: int = 30) -> list[str]:
    """Search Wikipedia for article titles matching a query."""
    params = {
        "action": "query", "list": "search", "srsearch": query,
        "srlimit": limit, "format": "json",
    }
    try:
        resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return [r["title"] for r in resp.json().get("query", {}).get("search", [])]
    except Exception as e:
        logger.warning("Wiki search '%s' failed: %s", query, e)
    return []


def wiki_batch_extract(titles: list[str]) -> list[dict]:
    """Batch-fetch extracts for multiple titles in one API call."""
    entries = []
    # Split into chunks of 20 (API max)
    for i in range(0, len(titles), 20):
        chunk = titles[i:i+20]
        params = {
            "action": "query", "titles": "|".join(chunk),
            "prop": "extracts", "explaintext": True,
            "exlimit": 20, "format": "json",
        }
        try:
            resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for pid, page in pages.items():
                    if pid == "-1":
                        continue
                    extract = page.get("extract", "")
                    if extract and len(extract) > 200:
                        entries.append({
                            "title": page["title"],
                            "content": extract[:8000],
                            "source": f"https://en.wikipedia.org/wiki/{page['title'].replace(' ', '_')}",
                            "type": "wikipedia",
                        })
        except Exception as e:
            logger.warning("Wiki batch failed: %s", e)
    return entries


def wiki_random_batch(count: int = 50) -> list[dict]:
    """Fetch random Wikipedia articles in bulk."""
    params = {
        "action": "query", "generator": "random", "grnnamespace": 0,
        "grnlimit": count, "prop": "extracts", "exintro": True,
        "explaintext": True, "format": "json",
    }
    try:
        resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return []
        pages = resp.json().get("query", {}).get("pages", {})
        entries = []
        for pid, page in pages.items():
            extract = page.get("extract", "")
            title = page.get("title", "")
            if title and extract and len(extract) > 200:
                entries.append({
                    "title": title,
                    "content": extract[:6000],
                    "source": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    "type": "wikipedia",
                })
        return entries
    except Exception as e:
        logger.warning("Wiki random failed: %s", e)
        return []


def fetch_wikipedia_topic(topic: str, keywords: list[str]) -> list[dict]:
    """Search Wikipedia for topic-related articles and fetch their extracts."""
    logger.info(f"Fetching Wikipedia topic: {topic} ({len(keywords)} keywords)")
    all_titles = set()
    for kw in keywords:
        found = wiki_search_titles(kw, limit=10)
        for t in found:
            all_titles.add(t)
        time.sleep(0.1)

    entries = wiki_batch_extract(list(all_titles))
    logger.info(f"  Got {len(entries)} articles for {topic}")
    return entries


# ─── Current News via Hacker News ───────────────────────────

def fetch_hn_top() -> list[dict]:
    """Fetch top Hacker News stories."""
    try:
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", headers=HEADERS, timeout=15)
        ids = resp.json()[:60]
    except Exception as e:
        logger.warning("HN top failed: %s", e)
        return []

    entries = []
    def get_story(item_id):
        try:
            r = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", headers=HEADERS, timeout=10)
            d = r.json()
            title = (d.get("title") or "").strip()
            if not title:
                return None
            text = (d.get("text") or d.get("url") or "")[:1000]
            return {"title": title, "content": text, "source": d.get("url") or f"https://news.ycombinator.com/item?id={item_id}", "type": "hackernews"}
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=20) as pool:
        for f in as_completed([pool.submit(get_story, i) for i in ids]):
            e = f.result()
            if e:
                entries.append(e)
    logger.info(f"HN top stories: {len(entries)} entries")
    return entries


# ─── Current News via Reddit ────────────────────────────────

NEWS_SUBREDDITS = [
    "news", "worldnews", "politics", "language", "linguistics",
    "technology", "science", "history", "grammar", "todayilearned",
    "explainlikeimfive", "futurology", "space", "anime", "gaming",
    "movies", "music", "books", "philosophy", "economics",
]

def fetch_reddit_hot(sub: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{sub}/hot.json?limit=15"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        entries = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            title = (d.get("title") or "").strip()
            if not title:
                continue
            selftext = (d.get("selftext") or d.get("url") or "")[:800]
            entries.append({"title": title, "content": selftext, "source": d.get("url") or f"https://reddit.com/r/{sub}", "type": f"reddit/{sub}"})
        return entries
    except Exception as e:
        logger.warning(f"Reddit r/{sub} failed: {e}")
        return []


# ─── Web search current events ─────────────────────────────

def web_search_current_events() -> list[dict]:
    """Search for June 2026 current events via DuckDuckGo."""
    queries = [
        "news today June 2026",
        "world news 2026",
        "politics news 2026",
        "technology news 2026",
        "science news 2026",
        "space news 2026",
    ]
    entries = []
    try:
        from ddgs import DDGS
        with DDGS() as d:
            for q in queries:
                try:
                    results = list(d.text(q, max_results=8))
                    for r in results:
                        title = (r.get("title") or "").strip()
                        href = r.get("href") or ""
                        body = (r.get("body") or "")[:500]
                        if title and href:
                            entries.append({"title": title, "content": body, "source": href, "type": "news_web"})
                except Exception as e:
                    logger.warning(f"Search '{q}' failed: {e}")
    except ImportError:
        logger.warning("ddgs not installed, skipping web search")
    logger.info(f"Web search results: {len(entries)} entries")
    return entries


# ─── Main ───────────────────────────────────────────────────

def seed_all():
    logger.info("=" * 60)
    logger.info("SEEDING KNOWLEDGE BASE")
    logger.info("=" * 60)

    before = stats()
    logger.info(f"Before: {before['total_entries']} entries, {before['total_chars']:,} chars")

    # Phase 1: Wikipedia random articles (bulk — get hundreds of articles fast)
    logger.info("Fetching random Wikipedia articles (batches of 50)...")
    all_wiki = []
    for batch in range(20):  # 20 batches × 50 = up to 1000 articles
        entries = wiki_random_batch(50)
        all_wiki.extend(entries)
        logger.info(f"  Batch {batch+1}/20: {len(entries)} articles (total wiki: {len(all_wiki)})")
        time.sleep(0.5)  # Rate limiting

    # Phase 2: Wikipedia topic searches (targeted high-value content)
    for topic, keywords in WIKI_TOPICS.items():
        entries = fetch_wikipedia_topic(topic, keywords)
        all_wiki.extend(entries)
        time.sleep(0.3)

    # Deduplicate by title
    seen_titles = set()
    unique_wiki = []
    for e in all_wiki:
        t = e.get("title", "")
        if t and t not in seen_titles:
            seen_titles.add(t)
            unique_wiki.append(e)
    logger.info(f"Wikipedia total (unique): {len(unique_wiki)} articles")

    # Phase 2: Current HN
    hn = fetch_hn_top()

    # Phase 3: Reddit
    reddit_entries = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        fut_map = {pool.submit(fetch_reddit_hot, sub): sub for sub in NEWS_SUBREDDITS}
        for f in as_completed(fut_map):
            reddit_entries.extend(f.result())

    # Phase 4: Web search current events
    web_entries = web_search_current_events()

    # Add all to knowledge base (batch, rebuild index only once)
    from knowledge import load, save
    existing = load()
    seen_sources = {e.get("source", "") for e in existing}

    added = 0
    for entry in unique_wiki + hn + reddit_entries + web_entries:
        src = entry.get("source", "")
        if src and src not in seen_sources:
            seen_sources.add(src)
            existing.append({
                "title": entry.get("title", "Untitled"),
                "content": entry.get("content", ""),
                "source": src,
                "type": entry.get("type", "text"),
            })
            added += 1

    save(existing)
    rebuild_index()
    after = stats()
    logger.info("=" * 60)
    logger.info(f"Added: {added} new entries")
    logger.info(f"Total: {after['total_entries']} entries, {after['total_chars']:,} chars")
    logger.info(f"File size: {after['file_size_mb']} MB")
    logger.info(f"By type: {json.dumps(after['type_breakdown'], indent=2)}")
    logger.info("=" * 60)
    return after


if __name__ == "__main__":
    seed_all()
