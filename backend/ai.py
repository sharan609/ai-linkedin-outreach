import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "You generate short LinkedIn connection request messages. "
    "Be professional, specific, human-sounding. Maximum 300 characters. "
    "No hashtags. No emojis. No generic templates."
)

def _build_user_prompt(recruiter: dict, user_skills: list) -> str:
    skills_str = ", ".join(user_skills) if user_skills else "various technical skills"
    return (
        f"Generate a LinkedIn outreach message for:\n"
        f"- Recruiter name: {recruiter.get('name', 'Recruiter')}\n"
        f"- Company: {recruiter.get('company', 'their company')}\n"
        f"- Hiring focus: {recruiter.get('focus', 'general')}\n"
        f"- Their headline: {recruiter.get('headline', '')}\n"
        f"- My skills: {skills_str}\n"
        f"Keep it under 300 characters."
    )

def _fallback_message(recruiter: dict, user_skills: list) -> str:
    name = recruiter.get("name", "there").split()[0]
    company = recruiter.get("company", "your company")
    skills = ", ".join(user_skills[:3]) if user_skills else "relevant technical skills"
    msg = (
        f"Hi {name}, I came across your profile and noticed you're "
        f"hiring at {company}. I have experience with {skills} and "
        f"would love to connect about potential opportunities."
    )
    return msg[:300]

def generate_message(recruiter: dict, user_skills: list) -> str:
    if not GROQ_API_KEY:
        print("[ai] No GROQ_API_KEY set — using fallback message", file=sys.stderr)
        return _fallback_message(recruiter, user_skills)

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(recruiter, user_skills)}
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }
        )
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text[:300]

    except Exception as e:
        print(f"[ai] Groq API error: {e}", file=sys.stderr)
        return _fallback_message(recruiter, user_skills)