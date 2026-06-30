"""Fast knowledge fill — blasts Wikipedia + news in parallel."""
import logging, time, json, requests, concurrent.futures
from knowledge import load, save, rebuild_index, stats, search

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
H = {"User-Agent": "VioraAI/1.0"}

WIKI_TOPICS = [
    "Politics", "Democracy", "Republic", "Constitution", "Election", "United_Nations", "European_Union",
    "Language", "Grammar", "Linguistics", "Syntax", "Semantics", "English_language", "Arabic", "Hindi",
    "World_War_II", "Cold_War", "French_Revolution", "Roman_Empire", "Renaissance",
    "Physics", "Chemistry", "Biology", "Artificial_intelligence", "Quantum_mechanics", "Evolution", "DNA",
    "Economics", "Stock_market", "Inflation", "Cryptocurrency", "Globalization",
    "Philosophy", "Ethics", "Logic", "Consciousness", "Religion",
    "Art", "Music", "Literature", "Film", "Architecture", "Poetry",
    "Geography", "Climate_change", "Solar_System", "Black_hole", "Internet",
    "Programming_language", "Computer_science", "Robotics", "Nanotechnology",
]

def wiki_batch(titles):
    entries = []
    for i in range(0, len(titles), 50):
        params = {"action":"query","titles":"|".join(titles[i:i+50]),"prop":"extracts","explaintext":1,"exlimit":50,"format":"json"}
        for _ in range(3):
            try:
                r = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=H, timeout=30)
                if r.status_code == 200:
                    for pid, p in r.json()["query"]["pages"].items():
                        if pid != "-1" and p.get("extract","") and len(p["extract"]) > 200:
                            entries.append({"title":p["title"],"content":p["extract"][:8000],"source":f"https://en.wikipedia.org/wiki/{p['title'].replace(' ','_')}","type":"wikipedia"})
                    break
            except requests.exceptions.RequestException as e:
                logger.warning(f"Wikipedia API error: {e}")
                time.sleep(3)
        time.sleep(0.3)
    return entries

def wiki_search(keyword, limit=15):
    params = {"action":"query","list":"search","srsearch":keyword,"srlimit":limit,"format":"json"}
    for _ in range(3):
        try:
            r = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=H, timeout=15)
            if r.status_code == 200:
                return [x["title"] for x in r.json()["query"]["search"]]
        except requests.exceptions.RequestException as e:
            logger.warning(f"Wikipedia search error: {e}")
            time.sleep(2)
    return []

def wiki_random(batch_size=50, batches=10):
    entries = []
    for b in range(batches):
        params = {"action":"query","generator":"random","grnnamespace":0,"grnlimit":batch_size,"prop":"extracts","exintro":1,"explaintext":1,"format":"json"}
        for _ in range(3):
            try:
                r = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=H, timeout=30)
                if r.status_code == 200:
                    for pid, p in r.json()["query"]["pages"].items():
                        if p.get("extract","") and len(p["extract"]) > 200:
                            entries.append({"title":p["title"],"content":p["extract"][:6000],"source":f"https://en.wikipedia.org/wiki/{p['title'].replace(' ','_')}","type":"wikipedia"})
                    break
            except requests.exceptions.RequestException as e:
                logger.warning(f"Wikipedia random error: {e}")
                time.sleep(3)
        time.sleep(0.5)
        logger.info(f"  random batch {b+1}/{batches}: {len(entries)} total")
    return entries

def fetch_hn():
    try:
        ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", headers=H, timeout=15).json()[:80]
    except requests.exceptions.RequestException as e:
        logger.warning(f"Hacker News error: {e}")
        return []
    def get(i):
        for _ in range(2):
            try:
                d = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json", headers=H, timeout=10).json()
                if d.get("title"):
                    return {"title":d["title"],"content":(d.get("text") or d.get("url") or "")[:1000],"source":d.get("url") or f"https://news.ycombinator.com/item?id={i}","type":"hackernews"}
            except requests.exceptions.RequestException as e:
                logger.warning(f"HN item error for id {i}: {e}")
                time.sleep(1)
        return None
    with concurrent.futures.ThreadPoolExecutor(30) as ex:
        return [r for r in ex.map(get, ids) if r]

def fetch_reddit():
    entries = []
    subs = ["news","worldnews","politics","language","linguistics","technology","science","history","todayilearned","futurology","philosophy","grammar","books","economics"]
    for sub in subs:
        for _ in range(2):
            try:
                r = requests.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=10", headers=H, timeout=10)
                if r.status_code == 200:
                    for c in r.json()["data"]["children"]:
                        d = c["data"]
                        if d.get("title"):
                            entries.append({"title":d["title"],"content":(d.get("selftext") or d.get("url") or "")[:800],"source":d.get("url") or f"https://reddit.com/r/{sub}","type":f"reddit/{sub}"})
                    break
            except requests.exceptions.RequestException as e:
                logger.warning(f"Reddit r/{sub} error: {e}")
                time.sleep(1)
    return entries

def run():
    before = stats()
    logger.info(f"BEFORE: {before['total_entries']} entries, {before['total_chars']:,} chars")
    existing = load()
    seen = {e.get("source","") for e in existing}

    def add(new, label):
        n = 0
        for e in new:
            s = e.get("source","")
            if s and s not in seen:
                seen.add(s); existing.append(e); n += 1
        logger.info(f"  +{n} {label}")
        return n

    total = 0

    # Phase 1: Topic searches → batch fetch
    logger.info("Step 1: Searching Wikipedia topics...")
    all_titles = set()
    for topic in WIKI_TOPICS:
        for t in wiki_search(topic):
            all_titles.add(t)
        time.sleep(0.1)
    logger.info(f"  Found {len(all_titles)} unique article titles")

    logger.info("Step 2: Batch-fetching articles...")
    wiki_entries = wiki_batch(list(all_titles))
    total += add(wiki_entries, "Wikipedia topic articles")

    # Phase 3: Random Wikipedia
    logger.info("Step 3: Random Wikipedia articles...")
    random_entries = wiki_random(batches=10)
    total += add(random_entries, "random Wikipedia")

    # Phase 4: Current news
    logger.info("Step 4: News...")
    hn = fetch_hn(); total += add(hn, "Hacker News")
    reddit = fetch_reddit(); total += add(reddit, "Reddit")

    # Save
    save(existing)
    rebuild_index()

    after = stats()
    logger.info("=" * 60)
    logger.info(f"ADDED: {total} new entries")
    logger.info(f"TOTAL: {after['total_entries']} entries, {after['total_chars']:,} chars, {after['file_size_mb']} MB")
    logger.info(f"Types: {json.dumps(after['type_breakdown'], indent=2)}")
    logger.info("=" * 60)

    # Verify
    for q in ["politics democracy", "language grammar", "world war", "science AI", "economics", "philosophy"]:
        r = search(q, top_k=2)
        if r: logger.info(f"  '{q}' → {r[0]['title']} ({r[0]['score']})")
        else: logger.info(f"  '{q}' → no results")

if __name__ == "__main__":
    run()
