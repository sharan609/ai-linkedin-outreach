"""
scraper.py — Selenium-based LinkedIn profile scraper.

Uses headless Chrome to load public LinkedIn profiles and extracts
key recruiter data (name, headline, company, about section).
"""

import sys
import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
)


def _create_driver() -> webdriver.Chrome:
    """Create a headless Chrome WebDriver instance."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(options=opts)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def _safe_text(driver, by, selector: str, default: str = "") -> str:
    """Extract text from an element, returning default on failure."""
    try:
        el = driver.find_element(by, selector)
        return (el.text or "").strip()
    except (NoSuchElementException, Exception):
        return default


def scrape_profile(url: str) -> dict:
    """
    Scrape a single LinkedIn profile page.

    Args:
        url: Full LinkedIn profile URL.

    Returns:
        Dict with keys: name, headline, company, about, raw_text, url.
        On failure: dict with keys: error, url.
    """
    driver = None
    try:
        driver = _create_driver()
        driver.set_page_load_timeout(15)
        driver.get(url)

        # Random human-like delay
        time.sleep(random.uniform(2.0, 4.0))

        # Wait for the profile name to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )

        # Extract fields
        name = _safe_text(driver, By.CSS_SELECTOR, "h1")

        # Headline — multiple possible selectors
        headline = (
            _safe_text(driver, By.CSS_SELECTOR, "div.text-body-medium")
            or _safe_text(driver, By.CSS_SELECTOR, ".pv-text-details__left-panel .text-body-medium")
        )

        # Company — try the experience section or top card
        company = (
            _safe_text(driver, By.CSS_SELECTOR, "[data-field='experience_company_logo'] span")
            or _safe_text(driver, By.CSS_SELECTOR, ".pv-text-details__right-panel span")
            or ""
        )

        # About section
        about = ""
        try:
            about_section = driver.find_element(
                By.CSS_SELECTOR,
                "#about ~ div .pv-shared-text-with-see-more span[aria-hidden='true']"
            )
            about = (about_section.text or "")[:500].strip()
        except Exception:
            pass

        raw_text = f"{name} {headline} {about}".strip()

        return {
            "name": name or "Unknown",
            "headline": headline,
            "company": company,
            "about": about,
            "raw_text": raw_text,
            "url": url,
        }

    except TimeoutException:
        msg = f"Timeout loading profile: {url}"
        print(f"[scraper] {msg}", file=sys.stderr)
        return {"error": msg, "url": url}
    except WebDriverException as e:
        msg = f"WebDriver error for {url}: {e.msg if hasattr(e, 'msg') else str(e)}"
        print(f"[scraper] {msg}", file=sys.stderr)
        return {"error": msg, "url": url}
    except Exception as e:
        msg = f"Unexpected error scraping {url}: {e}"
        print(f"[scraper] {msg}", file=sys.stderr)
        return {"error": msg, "url": url}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def scrape_profiles(urls: list[str]) -> list[dict]:
    """
    Scrape multiple LinkedIn profiles sequentially.

    Skips individual failures without crashing the batch.

    Args:
        urls: List of LinkedIn profile URLs.

    Returns:
        List of successfully scraped profile dicts.
    """
    results: list[dict] = []
    for url in urls:
        profile = scrape_profile(url)
        if "error" not in profile:
            results.append(profile)
        else:
            print(f"[scraper] Skipping failed profile: {url}", file=sys.stderr)
    return results
