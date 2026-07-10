from typing import Optional, List
from pydantic import BaseModel
import re

class NormalizedJob(BaseModel):
    title: str
    company: str
    location: str
    employment_type: str = "Full-time"
    remote_status: str = "Unknown"
    yoe_required: Optional[int] = None
    salary_range: Optional[str] = None
    industry: Optional[str] = None
    responsibilities: List[str] = []
    qualifications: List[str] = []
    description_text: str
    apply_url: str
    posted_date: Optional[str] = None

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

def normalize_apify_job(raw_job: dict) -> NormalizedJob:
    """
    Normalizes a raw job dictionary from Apify into a canonical NormalizedJob.
    """
    title = raw_job.get("title") or raw_job.get("jobTitle") or "Unknown Role"
    company = raw_job.get("companyName") or raw_job.get("company") or "Unknown Company"
    location = raw_job.get("location") or raw_job.get("jobLocation") or "Unknown Location"
    apply_url = raw_job.get("url") or raw_job.get("link") or raw_job.get("applyUrl") or ""
    description_text = raw_job.get("descriptionText") or raw_job.get("description") or ""

    # Basic Remote inference
    remote_status = "Remote" if "remote" in location.lower() or "remote" in title.lower() else "On-site/Hybrid"

    # YOE Extraction
    yoe = _extract_required_yoe(description_text)

    employment_type = raw_job.get("employmentType", "Full-time")
    salary_range = raw_job.get("salaryRange")

    return NormalizedJob(
        title=title,
        company=company,
        location=location,
        employment_type=employment_type,
        remote_status=remote_status,
        yoe_required=yoe,
        salary_range=salary_range,
        description_text=description_text,
        apply_url=apply_url
    )
