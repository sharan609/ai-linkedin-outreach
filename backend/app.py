"""
app.py — FastAPI application for the AI LinkedIn Outreach Assistant.

Provides the POST /find endpoint that orchestrates search → scrape →
analyze → AI message generation, with automatic mock-data fallback.
"""

import sys
import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from search import find_recruiter_urls
# from scraper import scrape_profiles
from analyzer import detect_focus
from ai import generate_message

# ── App setup ─────────────────────────────────────────────────
app = FastAPI(
    title="LinkedIn Outreach Assistant API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request timeout (90 s) ────────────────────────────────────
REQUEST_TIMEOUT = 90
MAX_RESULTS = 15

# ── Mock data ─────────────────────────────────────────────────
MOCK_RECRUITERS = [
    {
        "name": "Rahul Sharma",
        "headline": "Senior Technical Recruiter at Infosys",
        "company": "Infosys",
        "focus": "backend",
        "message": "Hi Rahul, I noticed you hire backend engineers at Infosys. I have strong C++ and Node.js experience and would love to connect about opportunities.",
        "url": "https://linkedin.com/in/rahul-sharma-example",
        "source": "mock",
    },
    {
        "name": "Priya Nair",
        "headline": "Campus Recruiter | Hiring Interns | Bangalore",
        "company": "Wipro",
        "focus": "internship",
        "message": "Hi Priya, I saw you're hiring interns at Wipro. I'm a CS student with React and DSA skills and would love to connect.",
        "url": "https://linkedin.com/in/priya-nair-example",
        "source": "mock",
    },
    {
        "name": "Ankit Verma",
        "headline": "Frontend Engineering Recruiter at Flipkart",
        "company": "Flipkart",
        "focus": "frontend",
        "message": "Hi Ankit, I came across your profile and saw you recruit frontend engineers at Flipkart. I specialize in React, TypeScript, and UI/UX and would love to explore opportunities.",
        "url": "https://linkedin.com/in/ankit-verma-example",
        "source": "mock",
    },
    {
        "name": "Megha Reddy",
        "headline": "Tech Talent Partner — Full Stack Roles | TCS",
        "company": "TCS",
        "focus": "fullstack",
        "message": "Hi Megha, I noticed you're hiring full-stack developers at TCS. With experience in Node.js, React, and PostgreSQL, I'd love to discuss how I can contribute.",
        "url": "https://linkedin.com/in/megha-reddy-example",
        "source": "mock",
    },
    {
        "name": "Siddharth Joshi",
        "headline": "AI/ML Talent Acquisition Lead at Google DeepMind",
        "company": "Google DeepMind",
        "focus": "ai_ml",
        "message": "Hi Siddharth, I'm excited to see you lead AI/ML hiring at Google DeepMind. I have published research in NLP and hands-on PyTorch experience — would love to connect.",
        "url": "https://linkedin.com/in/siddharth-joshi-example",
        "source": "mock",
    },
]


# ── Request / response models ─────────────────────────────────
class FindRequest(BaseModel):
    role: str
    location: str
    user_skills: Optional[list[str]] = None

    @field_validator("role", "location")
    @classmethod
    def must_be_non_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must be a non-empty string")
        return v.strip()


class RegenerateRequest(BaseModel):
    recruiter_url: str
    recruiter_data: dict
    user_skills: Optional[str] = ""


# ── Helpers ────────────────────────────────────────────────────
def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", file=sys.stderr)


def _process_profiles(profiles: list[dict], user_skills: list[str]) -> list[dict]:
    """Analyze focus and generate messages for scraped profiles."""
    results: list[dict] = []
    for p in profiles[:MAX_RESULTS]:
        try:
            focus = detect_focus(p.get("raw_text", ""))
            p["focus"] = focus
            p["message"] = generate_message(p, user_skills)
            p["source"] = "scraped"
            # Remove raw_text / about from response (internal only)
            results.append({
                "name": p.get("name", "Unknown"),
                "headline": p.get("headline", ""),
                "company": p.get("company", ""),
                "focus": focus,
                "message": p["message"],
                "url": p.get("url", ""),
                "source": "scraped",
            })
        except Exception as e:
            _log(f"Skipping profile due to error: {e}")
            continue
    return results


# ── Routes ─────────────────────────────────────────────────────
@app.post("/find")
async def find_recruiters(body: FindRequest):
    """
    Main endpoint: find LinkedIn recruiters, scrape profiles,
    classify focus, and generate AI outreach messages.
    """
    _log(f"POST /find — role={body.role!r}, location={body.location!r}")
    user_skills = body.user_skills or []

    try:
        # Run the blocking pipeline in a thread with timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(_pipeline, body.role, body.location, user_skills),
            timeout=REQUEST_TIMEOUT,
        )
        return result

    except asyncio.TimeoutError:
        _log("Request timed out after 90 seconds")
        return JSONResponse(
            status_code=504,
            content={"error": "Request timed out. Please try again.", "code": "TIMEOUT"},
        )
    except Exception as e:
        _log(f"Unhandled error in /find: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "code": "INTERNAL_ERROR"},
        )


def _pipeline(role: str, location: str, user_skills: list[str]) -> list[dict]:
    """Synchronous pipeline: search → analyze → generate (no Selenium needed)."""

    # Step 1: Search Google for recruiter profiles
    _log("Step 1/2: Searching Google for recruiter profiles…")
    profiles = find_recruiter_urls(role, location)
    _log(f"Found {len(profiles)} profiles from Google")

    if not profiles:
        _log("No profiles found — returning mock data")
        return MOCK_RECRUITERS

    # Step 2: Analyze & generate messages
    _log("Step 2/2: Analyzing focus & generating messages…")
    results = _process_profiles(profiles, user_skills)

    if not results:
        _log("Processing returned 0 results — returning mock data")
        return MOCK_RECRUITERS

    _log(f"Returning {len(results)} recruiter(s)")
    return results


@app.post("/regenerate")
async def regenerate_message(body: RegenerateRequest):
    """Regenerate a single recruiter's outreach message."""
    _log(f"POST /regenerate — url={body.recruiter_url!r}")

    skills = [s.strip() for s in body.user_skills.split(",") if s.strip()] if body.user_skills else []

    try:
        msg = await asyncio.to_thread(generate_message, body.recruiter_data, skills)
        return {"message": msg}
    except Exception as e:
        _log(f"Regeneration failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to regenerate message", "code": "AI_FAILURE"},
        )


# ── Validation error handler ──────────────────────────────────
@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid input — role and location are required.",
            "code": "INVALID_INPUT",
        },
    )


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
