"""
search.py — SerpAPI-powered LinkedIn recruiter search.
No CAPTCHAs, clean JSON results, 100 free searches/month.
"""

import os
import sys
import re
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

EXCLUDED_PATHS = ("/company/", "/jobs/", "/posts/", "/pulse/", "/learning/")


def _is_valid_profile_url(url: str) -> bool:
    parsed = urlparse(url)
    if "linkedin.com" not in parsed.netloc:
        return False
    if "/in/" not in parsed.path:
        return False
    for ex in EXCLUDED_PATHS:
        if ex in parsed.path:
            return False
    return True


def _extract_company(text: str) -> str:
    for marker in [" at ", " @ ", " - "]:
        if marker in text:
            part = text.split(marker)[-1]
            return part.split("|")[0].split("·")[0].strip()
    return "Unknown"


def find_recruiter_urls(role: str, location: str, max_results: int = 10) -> list[dict]:
    """
    Search Google via SerpAPI for LinkedIn recruiter profiles.
    Returns list of profile dicts ready for analyzer + ai pipeline.
    """
    if not SERPAPI_KEY:
        print("[search] No SERPAPI_KEY found in .env", file=sys.stderr)
        return []

    try:
        # pyrefly: ignore [missing-import]
        from serpapi import GoogleSearch
    except ImportError:
        print("[search] serpapi not installed — run: pip install google-search-results", file=sys.stderr)
        return []

    query = (
    f'site:linkedin.com/in '
    f'("recruiter" OR "talent acquisition" OR "hiring manager") '
    f'"{location}"'
)

    all_results: list[dict] = []
    seen_urls: set[str] = set()

    for start in (0, 10):
        if len(all_results) >= max_results:
            break

        try:
            search = GoogleSearch({
                "q": query,
                "start": start,
                "num": 10,
                "hl": "en",
                "api_key": SERPAPI_KEY,
            })
            data = search.get_dict()
            organic = data.get("organic_results", [])
            print(f"[search] SerpAPI start={start}: {len(organic)} raw results", file=sys.stderr)

            for item in organic:
                url = item.get("link", "").split("?")[0].rstrip("/")
                if not _is_valid_profile_url(url) or url in seen_urls:
                    continue
                seen_urls.add(url)

                # Parse title — usually "Name - Title at Company | LinkedIn"
                title = item.get("title", "")
                title = re.sub(r"\s*\|\s*LinkedIn.*$", "", title).strip()
                title = re.sub(r"\s*-\s*LinkedIn.*$", "", title).strip()

                if " - " in title:
                    name = title.split(" - ")[0].strip()
                    headline = " - ".join(title.split(" - ")[1:]).strip()
                else:
                    name = title.strip()
                    headline = ""

                snippet = item.get("snippet", "")

                if not headline and snippet:
                    headline = snippet[:120]

                company = _extract_company(headline) if headline else _extract_company(snippet)
                raw_text = f"{name} {headline} {snippet}".strip()

                all_results.append({
                    "name": name or "Unknown",
                    "headline": headline,
                    "company": company,
                    "about": snippet,
                    "raw_text": raw_text,
                    "url": url,
                    "source": "serpapi",
                })

        except Exception as e:
            print(f"[search] SerpAPI error (start={start}): {e}", file=sys.stderr)

    print(f"[search] Total profiles found: {len(all_results[:max_results])}", file=sys.stderr)
    return all_results[:max_results]