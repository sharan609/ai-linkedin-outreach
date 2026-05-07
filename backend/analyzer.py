"""
analyzer.py — Keyword-based hiring focus detector.

Classifies recruiter profiles into focus categories based on
keyword matching with a priority ordering system.
"""

import re

# Categories ordered by priority (highest first)
FOCUS_KEYWORDS: dict[str, list[str]] = {
    "internship": [
        "intern", "internship", "campus", "fresher",
        "entry level", "entry-level", "graduate",
    ],
    "ai_ml": [
        "machine learning", "ml", "ai", "data science",
        "nlp", "deep learning", "artificial intelligence",
    ],
    "backend": [
        "backend", "back-end", "back end", "server-side",
        "server side", "java", "python dev", "golang", "node.js",
    ],
    "frontend": [
        "frontend", "front-end", "front end", "react",
        "vue", "angular", "ui engineer",
    ],
    "fullstack": [
        "full stack", "full-stack", "fullstack", "mern", "mean",
    ],
}

# Priority order for conflict resolution
PRIORITY = ["internship", "ai_ml", "backend", "frontend", "fullstack"]


def detect_focus(raw_text: str) -> str:
    """
    Classify recruiter focus from their profile text.

    Uses case-insensitive keyword matching. When multiple categories
    match, returns the one with highest priority.

    Args:
        raw_text: Concatenated profile text (name + headline + about).

    Returns:
        One of: internship, ai_ml, backend, frontend, fullstack, general.
    """
    if not raw_text:
        return "general"

    text_lower = raw_text.lower()
    matched: set[str] = set()

    for category, keywords in FOCUS_KEYWORDS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                matched.add(category)
                break  # One keyword match is enough per category

    if not matched:
        return "general"

    # Return highest-priority match
    for cat in PRIORITY:
        if cat in matched:
            return cat

    return "general"
