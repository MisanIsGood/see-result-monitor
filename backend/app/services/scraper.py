"""
SEE Result Scraper
Polls multiple official and semi-official portals to detect when
a student's SEE result has been published, then extracts data.
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3


@dataclass
class SEEResult:
    """Holds a successfully scraped SEE result."""
    symbol_number: str
    name: str = ""
    school: str = ""
    district: str = ""
    gpa: str = ""
    grade: str = ""
    subjects: dict = field(default_factory=dict)
    result_status: str = ""   # e.g. "Passed", "Not Graded"
    source_url: str = ""
    raw_text: str = ""
    found: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """Strip extra whitespace from scraped text."""
    return re.sub(r"\s+", " ", text or "").strip()


def _parse_subjects_from_table(soup: BeautifulSoup) -> dict:
    """Extract subject-grade pairs from a result HTML table."""
    subjects = {}
    try:
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = [_clean_text(c.get_text()) for c in row.find_all(["td", "th"])]
                if len(cols) >= 2:
                    key, val = cols[0], cols[1]
                    if key and val and key.lower() not in ("subject", "s.n.", "#", "sn"):
                        subjects[key] = val
    except Exception as e:
        logger.debug(f"Could not parse subject table: {e}")
    return subjects


# ---------------------------------------------------------------------------
# Portal implementations
# ---------------------------------------------------------------------------

async def _check_ntc_see(
    client: httpx.AsyncClient, symbol: str, dob: str
) -> Optional[SEEResult]:
    """
    Check see.ntc.net.np (Nepal Telecom SEE portal).
    The site accepts a POST form with symbol number and DOB.
    """
    url = "https://see.ntc.net.np/"
    result_url = "https://see.ntc.net.np/result"

    try:
        # First GET to obtain any CSRF tokens / session cookies
        resp = await client.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        # POST form data
        form_data = {
            "symbol": symbol,
            "dob": dob,
        }
        post_resp = await client.post(result_url, data=form_data, timeout=REQUEST_TIMEOUT)

        if post_resp.status_code not in (200, 201):
            logger.debug(f"NTC SEE portal returned {post_resp.status_code}")
            return None

        soup = BeautifulSoup(post_resp.text, "lxml")

        # Check for "not found" indicators
        page_text = _clean_text(soup.get_text())
        not_found_keywords = [
            "result not found", "not published", "record not found",
            "invalid symbol", "no record", "सकिएको छैन"
        ]
        for kw in not_found_keywords:
            if kw.lower() in page_text.lower():
                logger.debug(f"NTC portal: result not found for {symbol}")
                return None

        # Try to find GPA / result info
        gpa_match = re.search(r"GPA[\s:]+([0-9.]+)", page_text, re.IGNORECASE)
        grade_match = re.search(r"Grade[\s:]+([A-Z][+]?)", page_text, re.IGNORECASE)
        name_match = re.search(r"Name[\s:]+([A-Za-z\s]+)", page_text, re.IGNORECASE)

        # Only treat as found if we see GPA or grade data
        if not gpa_match and not grade_match:
            return None

        res = SEEResult(
            symbol_number=symbol,
            name=_clean_text(name_match.group(1)) if name_match else "",
            gpa=gpa_match.group(1) if gpa_match else "",
            grade=grade_match.group(1) if grade_match else "",
            subjects=_parse_subjects_from_table(soup),
            source_url="https://see.ntc.net.np/",
            raw_text=page_text[:3000],
            found=True,
        )
        # Attempt status
        if "passed" in page_text.lower():
            res.result_status = "Passed"
        elif "not graded" in page_text.lower() or "ng" in page_text.lower():
            res.result_status = "Not Graded"
        else:
            res.result_status = "Result Available"

        logger.info(f"✅ NTC portal: result FOUND for {symbol}")
        return res

    except httpx.TimeoutException:
        logger.warning(f"NTC portal timeout for {symbol}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"NTC portal HTTP error {e.response.status_code} for {symbol}")
        return None
    except Exception as e:
        logger.error(f"NTC portal unexpected error for {symbol}: {e}")
        return None


async def _check_neb_gov(
    client: httpx.AsyncClient, symbol: str, dob: str
) -> Optional[SEEResult]:
    """
    Check result.neb.gov.np (official NEB result portal).
    """
    url = "https://result.neb.gov.np/"
    try:
        resp = await client.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Find form action
        form = soup.find("form")
        action = url
        if form and form.get("action"):
            action_path = form.get("action", "")
            if action_path.startswith("http"):
                action = action_path
            else:
                action = f"https://result.neb.gov.np{action_path}"

        form_data = {"symbol": symbol, "dob": dob}
        # Also add hidden fields
        if form:
            for hidden in form.find_all("input", type="hidden"):
                if hidden.get("name"):
                    form_data[hidden["name"]] = hidden.get("value", "")

        post_resp = await client.post(action, data=form_data, timeout=REQUEST_TIMEOUT)
        page_text = _clean_text(BeautifulSoup(post_resp.text, "lxml").get_text())

        gpa_match = re.search(r"GPA[\s:]+([0-9.]+)", page_text, re.IGNORECASE)
        grade_match = re.search(r"Grade[\s:]+([A-Z][+]?)", page_text, re.IGNORECASE)

        if not gpa_match and not grade_match:
            return None

        res = SEEResult(
            symbol_number=symbol,
            gpa=gpa_match.group(1) if gpa_match else "",
            grade=grade_match.group(1) if grade_match else "",
            source_url="https://result.neb.gov.np/",
            raw_text=page_text[:3000],
            found=True,
            result_status="Result Available",
        )
        logger.info(f"✅ NEB.GOV portal: result FOUND for {symbol}")
        return res

    except Exception as e:
        logger.debug(f"NEB.GOV portal error for {symbol}: {e}")
        return None


async def _check_edusanjal(
    client: httpx.AsyncClient, symbol: str, dob: str
) -> Optional[SEEResult]:
    """
    Check see.edusanjal.com (popular third-party SEE portal).
    """
    url = "https://see.edusanjal.com/"
    try:
        resp = await client.get(url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(resp.text, "lxml")

        form_data = {"symbol": symbol, "dob": dob}
        if soup.find("form"):
            for hidden in soup.find("form").find_all("input", type="hidden"):
                if hidden.get("name"):
                    form_data[hidden["name"]] = hidden.get("value", "")

        post_resp = await client.post(url, data=form_data, timeout=REQUEST_TIMEOUT)
        page_text = _clean_text(BeautifulSoup(post_resp.text, "lxml").get_text())

        gpa_match = re.search(r"GPA[\s:]+([0-9.]+)", page_text, re.IGNORECASE)
        if not gpa_match:
            return None

        res = SEEResult(
            symbol_number=symbol,
            gpa=gpa_match.group(1),
            source_url="https://see.edusanjal.com/",
            raw_text=page_text[:3000],
            found=True,
            result_status="Result Available",
        )
        logger.info(f"✅ Edusanjal: result FOUND for {symbol}")
        return res

    except Exception as e:
        logger.debug(f"Edusanjal error for {symbol}: {e}")
        return None


async def _check_collegeinfo(
    client: httpx.AsyncClient, symbol: str, dob: str
) -> Optional[SEEResult]:
    """
    Check collegeinfo.com.np/see-result portal.
    """
    url = "https://collegeinfo.com.np/see-result/"
    try:
        resp = await client.get(url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(resp.text, "lxml")

        form_data = {"symbol": symbol, "dob": dob}
        form = soup.find("form")
        if form:
            action = form.get("action", url)
            if not action.startswith("http"):
                action = f"https://collegeinfo.com.np{action}"
            for hidden in form.find_all("input", type="hidden"):
                if hidden.get("name"):
                    form_data[hidden["name"]] = hidden.get("value", "")
        else:
            action = url

        post_resp = await client.post(action, data=form_data, timeout=REQUEST_TIMEOUT)
        page_text = _clean_text(BeautifulSoup(post_resp.text, "lxml").get_text())

        gpa_match = re.search(r"GPA[\s:]+([0-9.]+)", page_text, re.IGNORECASE)
        if not gpa_match:
            return None

        res = SEEResult(
            symbol_number=symbol,
            gpa=gpa_match.group(1),
            source_url="https://collegeinfo.com.np/see-result/",
            raw_text=page_text[:3000],
            found=True,
            result_status="Result Available",
        )
        logger.info(f"✅ CollegeInfo: result FOUND for {symbol}")
        return res

    except Exception as e:
        logger.debug(f"CollegeInfo error for {symbol}: {e}")
        return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

async def check_see_result(symbol_number: str, date_of_birth: str) -> Optional[SEEResult]:
    """
    Try all SEE portals concurrently. Return the first successful result.
    Raises no exceptions — all errors are logged internally.
    """
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        tasks = [
            _check_ntc_see(client, symbol_number, date_of_birth),
            _check_neb_gov(client, symbol_number, date_of_birth),
            _check_edusanjal(client, symbol_number, date_of_birth),
            _check_collegeinfo(client, symbol_number, date_of_birth),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, SEEResult) and r.found:
                return r

        return None


async def check_result_with_retry(
    symbol_number: str, date_of_birth: str, retries: int = MAX_RETRIES
) -> Optional[SEEResult]:
    """
    Wrap check_see_result with retry logic and exponential back-off.
    """
    for attempt in range(1, retries + 1):
        try:
            result = await check_see_result(symbol_number, date_of_birth)
            if result:
                return result
        except Exception as e:
            logger.error(f"Attempt {attempt}/{retries} failed for {symbol_number}: {e}")

        if attempt < retries:
            wait = 2 ** attempt
            logger.debug(f"Retry in {wait}s for {symbol_number}")
            await asyncio.sleep(wait)

    return None
