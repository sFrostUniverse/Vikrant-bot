import requests
from bs4 import BeautifulSoup

def get_top_indian_express_headlines(limit=5):
    url = "https://indianexpress.com/"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
    except Exception as e:
        print(f"[Scraper] Error fetching Indian Express: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    headlines = []
    seen = set()

    # Try multiple selectors to be resilient
    selectors = [
        "div.title a",                # Common for most headlines
        "div.more-news a",            # Some headline containers
        "div.nation a",               # National headlines
        "a[href^='https://indianexpress.com/article']"  # General article links
    ]

    for selector in selectors:
        for item in soup.select(selector):
            title = item.get_text(strip=True)
            link = item.get("href", "")
            if title and link.startswith("http") and link not in seen:
                seen.add(link)
                headlines.append((title, link))
                if len(headlines) >= limit:
                    return headlines

    return headlines
