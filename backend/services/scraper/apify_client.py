"""
Apify LinkedIn Job Scraper Client
Wraps the official apify-client v3.x SDK (Pydantic model returns).
"""
import logging
import re
import urllib.parse
from typing import Optional
from apify_client import ApifyClient as OfficialApifyClient
from backend.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# YOE regex filter — pure Python, no LLM (per contract)
# Rejects only when the JD *explicitly* requires > (candidate_yoe + 3) years.
# Default candidate YOE assumed = 2 (fresh-mid). Parsed from resume if passed.
# ---------------------------------------------------------------------------
YOE_PATTERNS = [
    r'(\d+)\+?\s*(?:to\s*\d+\s*)?years?\s+(?:of\s+)?(?:experience|exp)',
    r'minimum\s+(\d+)\s+years?',
    r'at\s+least\s+(\d+)\s+years?',
    r'(\d+)\s*-\s*(\d+)\s+years?',
]

def _extract_required_yoe(jd_text: str) -> Optional[int]:
    """Extract the minimum YOE requirement from a JD using regex only."""
    text_lower = jd_text.lower()
    min_req = None
    for pattern in YOE_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            groups = [g for g in match.groups() if g is not None]
            if groups:
                try:
                    yoe = int(groups[0])   # take the lower bound for ranges
                    if min_req is None or yoe < min_req:
                        min_req = yoe
                except ValueError:
                    continue
    return min_req


def yoe_filter(jd_text: str, candidate_yoe: int = 2) -> tuple[bool, str]:
    """
    Returns (should_include: bool, reason: str).
    Rejects ONLY when required > candidate_yoe + 3.
    If no YOE found in JD, always accepts.
    """
    required = _extract_required_yoe(jd_text)
    if required is None:
        return True, "No YOE requirement found — accepted"
    threshold = candidate_yoe + 3
    if required > threshold:
        return False, f"Requires {required}y, candidate has ~{candidate_yoe}y (threshold: {threshold}y)"
    return True, f"Requires {required}y — within threshold ({threshold}y)"


class ApifyClient:
    """Scrapes LinkedIn jobs via Apify. apify-client v3.x returns Pydantic models."""

    def __init__(self):
        self.api_token = settings.APIFY_API_TOKEN
        if not self.api_token:
            logger.warning("APIFY_API_TOKEN is not set — scraping disabled.")
            self.client = None
        else:
            self.client = OfficialApifyClient(self.api_token)

    def scrape_linkedin_jobs(self, role: str, location: str, count: int, posted_within: str = None) -> list[dict]:
        if not self.client:
            logger.error("Apify client not configured.")
            return []

        role_encoded = urllib.parse.quote(role)
        # Default to United States if no location provided to prevent 0 results
        location_encoded = urllib.parse.quote(location) if location else urllib.parse.quote("United States")

        url = f"https://www.linkedin.com/jobs/search?keywords={role_encoded}&location={location_encoded}"
        
        if posted_within:
            # Parse '24H', '1H', etc. to seconds
            match = re.search(r'(\d+)\s*H', posted_within.upper())
            if match:
                hours = int(match.group(1))
                seconds = hours * 3600
                url += f"&f_TPR=r{seconds}"
            elif posted_within.lower() == "past_week":
                url += "&f_TPR=r604800"

        run_input = {
            "count": count,
            "scrapeCompany": True,
            "splitByLocation": False,
            "urls": [url]
        }

        logger.info(f"Starting Apify Actor curious_coder/linkedin-jobs-scraper | url={url} | count={count}")

        try:
            # apify-client v3.x returns a Pydantic ActorRun model (or None)
            run = self.client.actor("curious_coder/linkedin-jobs-scraper").call(run_input=run_input)

            if run is None:
                logger.error("Actor returned None — likely aborted or timed out.")
                return []

            # v3.x uses snake_case Pydantic attributes
            dataset_id = getattr(run, "default_dataset_id", None)

            # Fallback: v2.x dict style (backwards compat)
            if dataset_id is None and isinstance(run, dict):
                dataset_id = run.get("defaultDatasetId")

            if not dataset_id:
                logger.error(f"Could not extract defaultDatasetId from run={run}")
                return []

            logger.info(f"Apify run succeeded. Dataset ID: {dataset_id}")

            jobs = []
            for item in self.client.dataset(dataset_id).iterate_items():
                title = item.get("title") or item.get("jobTitle") or ""
                company = item.get("companyName") or item.get("company") or ""
                location_val = item.get("location") or item.get("jobLocation") or ""
                url_val = item.get("url") or item.get("link") or item.get("applyUrl") or ""
                description = item.get("descriptionText") or item.get("description") or ""

                if not title or not company:
                    continue  # skip malformed entries

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location_val,
                    "url": url_val,
                    "description": description
                })

            logger.info(f"Scraped {len(jobs)} valid jobs from Apify dataset.")
            return jobs

        except Exception as e:
            logger.error(f"Apify scrape failed: {e}", exc_info=True)
            return []
