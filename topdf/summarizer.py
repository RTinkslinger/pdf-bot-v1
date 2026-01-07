"""
AI Summarization for topdf
==========================
Generates structured company analysis from pitch deck screenshots using Perplexity.

Pipeline:
1. OCR first 5 screenshots using pytesseract
2. Send text to Perplexity for analysis + peer search (single call)
3. Parse response into structured dataclasses
4. Generate markdown output
"""

import io
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .exceptions import OCRError, SummaryError

# Allowed sector tags
SECTORS = [
    "cybersecurity",
    "enterprise_tech",
    "consumer_tech",
    "consumer_goods",
    "fintech",
    "industrials",
    "robotics",
    "space_tech",
    "developer_tooling",
]

# Maximum pages to OCR
MAX_PAGES_TO_OCR = 5


@dataclass
class CompanyAnalysis:
    """Structured company information extracted from pitch deck."""

    company_name: str
    description: str  # ≤200 characters
    has_customers: bool
    customer_details: Optional[str]
    primary_sector: str
    secondary_sector: Optional[str]


@dataclass
class FundedPeer:
    """Recently funded peer company."""

    company_name: str
    round_type: str  # "Seed", "Series A", etc.
    amount: str  # "$10M"
    date: str  # "Jan 2024"
    description: Optional[str]


@dataclass
class StructuredSummary:
    """Complete structured summary with company analysis and peers."""

    company: CompanyAnalysis
    funded_peers: list[FundedPeer]


def check_tesseract() -> bool:
    """Check if Tesseract OCR is installed.

    Returns:
        True if tesseract is available, False otherwise.
    """
    return shutil.which("tesseract") is not None


def extract_text(screenshots: list[bytes], max_pages: int = MAX_PAGES_TO_OCR) -> str:
    """Extract text from screenshots using OCR.

    Args:
        screenshots: List of PNG screenshot bytes.
        max_pages: Maximum number of pages to process.

    Returns:
        Combined text from all processed pages.

    Raises:
        OCRError: If tesseract is not installed or extraction fails.
    """
    if not check_tesseract():
        raise OCRError("Tesseract not installed")

    # Import here to avoid import error if not installed
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise OCRError("pytesseract or Pillow not installed")

    texts = []
    for i, screenshot in enumerate(screenshots[:max_pages]):
        try:
            image = Image.open(io.BytesIO(screenshot))
            text = pytesseract.image_to_string(image)
            if text.strip():
                texts.append(f"--- Page {i + 1} ---\n{text.strip()}")
        except Exception as e:
            # Continue with other pages if one fails
            continue

    if not texts:
        raise OCRError("No text could be extracted from screenshots")

    return "\n\n".join(texts)


def _build_prompt(ocr_text: str) -> str:
    """Build the Perplexity prompt for analysis + peer search.

    Args:
        ocr_text: Extracted text from OCR.

    Returns:
        Formatted prompt string.
    """
    sectors_list = ", ".join(SECTORS)

    return f"""You are a venture capital analyst researching the competitive landscape for a startup.

PITCH DECK CONTENT:
{ocr_text}

---

## TASK 1: Company Analysis
Extract the following from the pitch deck:
- Company name
- What they do (200 chars max)
- Whether they have customers/traction
- Primary sector from: {sectors_list}

## TASK 2: Funded Peer Discovery (CRITICAL)
Search GLOBALLY for similar companies that have raised funding in the past 24 months.

**Search Strategy:**
1. First, identify the CORE PROBLEM the company is solving
2. Identify the PRODUCT CATEGORY (e.g., "AI code review", "supply chain visibility", "developer security")
3. Search for companies addressing the SAME problem or building SIMILAR products worldwide

**Where to look:**
- Crunchbase and PitchBook for funding data
- TechCrunch, Bloomberg for funding announcements
- LinkedIn for company profiles
- Regional sources: EU-Startups (Europe), Tech in Asia (APAC), etc.

**Include companies from:**
- North America
- Europe
- Asia-Pacific
- Middle East / Africa
- Latin America

**Funding criteria:**
- Round types: Pre-Seed, Seed, Series A, Series B
- Timeframe: Raised within last 24 months
- Find up to 10 peers with verified funding data

---

Return ONLY valid JSON (no markdown):
{{
  "company": {{
    "company_name": "string",
    "description": "string (max 200 chars)",
    "has_customers": boolean,
    "customer_details": "string or null",
    "primary_sector": "one of: {sectors_list}",
    "secondary_sector": "string or null"
  }},
  "funded_peers": [
    {{
      "company_name": "string",
      "round_type": "Pre-Seed/Seed/Series A/Series B",
      "amount": "$XM",
      "date": "Mon YYYY",
      "description": "One sentence about what they do"
    }}
  ]
}}"""


def _parse_response(response_text: str) -> StructuredSummary:
    """Parse Perplexity response into structured dataclasses.

    Args:
        response_text: Raw response from Perplexity.

    Returns:
        StructuredSummary with company analysis and peers.

    Raises:
        SummaryError: If response cannot be parsed.
    """
    # Try to extract JSON from response (may be wrapped in markdown)
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if not json_match:
        raise SummaryError("No JSON found in response")

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        raise SummaryError(f"Invalid JSON in response: {e}")

    # Parse company analysis
    company_data = data.get("company", {})
    if not company_data.get("company_name"):
        raise SummaryError("Missing company_name in response")

    # Validate sector
    primary_sector = company_data.get("primary_sector", "").lower().replace(" ", "_")
    if primary_sector not in SECTORS:
        # Try to find closest match or default
        primary_sector = "enterprise_tech"

    secondary_sector = company_data.get("secondary_sector")
    if secondary_sector:
        secondary_sector = secondary_sector.lower().replace(" ", "_")
        if secondary_sector not in SECTORS:
            secondary_sector = None

    # Truncate description if needed
    description = company_data.get("description", "")[:200]

    company = CompanyAnalysis(
        company_name=company_data.get("company_name", "Unknown"),
        description=description,
        has_customers=bool(company_data.get("has_customers", False)),
        customer_details=company_data.get("customer_details"),
        primary_sector=primary_sector,
        secondary_sector=secondary_sector,
    )

    # Parse funded peers
    peers = []
    for peer_data in data.get("funded_peers", [])[:10]:
        if peer_data.get("company_name"):
            peers.append(
                FundedPeer(
                    company_name=peer_data.get("company_name", ""),
                    round_type=peer_data.get("round_type", ""),
                    amount=peer_data.get("amount", ""),
                    date=peer_data.get("date", ""),
                    description=peer_data.get("description"),
                )
            )

    return StructuredSummary(company=company, funded_peers=peers)


def call_perplexity(api_key: str, ocr_text: str) -> StructuredSummary:
    """Call Perplexity API for analysis and peer search.

    Args:
        api_key: Perplexity API key.
        ocr_text: Extracted text from OCR.

    Returns:
        StructuredSummary with company analysis and peers.

    Raises:
        SummaryError: If API call fails.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise SummaryError("openai package not installed. Run: pip install topdf[summarize]")

    prompt = _build_prompt(ocr_text)

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai",
        )

        response = client.chat.completions.create(
            model="sonar-reasoning-pro",
            messages=[{"role": "user", "content": prompt}],
            extra_body={
                "search_domain_filter": [
                    # Funding databases
                    "crunchbase.com",
                    "news.crunchbase.com",
                    "pitchbook.com",
                    # Startup/VC news
                    "techcrunch.com",
                    "vcnewsdaily.com",
                    "techfundingnews.com",
                    "sifted.eu",
                    "fortune.com",
                    # Social/professional
                    "linkedin.com",
                    "twitter.com",
                    # Regional startup news
                    "eu-startups.com",
                    "techinasia.com",
                    "news.ycombinator.com",
                ],
                "search_recency_filter": "month",
            },
        )

        response_text = response.choices[0].message.content
        if not response_text:
            raise SummaryError("Empty response from Perplexity")

        return _parse_response(response_text)

    except Exception as e:
        if "openai" in str(type(e).__module__):
            raise SummaryError(f"Perplexity API error: {e}")
        raise


def format_markdown(summary: StructuredSummary) -> str:
    """Format structured summary as markdown.

    Args:
        summary: StructuredSummary to format.

    Returns:
        Formatted markdown string.
    """
    company = summary.company

    # Header
    lines = [f"# {company.company_name}", ""]

    # Overview
    lines.extend(["## Overview", company.description, ""])

    # Traction
    lines.append("## Traction")
    lines.append(f"**Early Customers:** {'Yes' if company.has_customers else 'No'}")
    if company.customer_details:
        lines.append(company.customer_details)
    lines.append("")

    # Sector
    lines.append("## Sector")
    lines.append(f"**Primary:** {company.primary_sector}")
    secondary = company.secondary_sector or "N/A"
    lines.append(f"**Secondary:** {secondary}")
    lines.append("")

    # Funded Peers
    lines.append("## Funded Peers (24-month lookback)")
    if summary.funded_peers:
        lines.append("| Company | Round | Amount | Date | Description |")
        lines.append("|---------|-------|--------|------|-------------|")
        for peer in summary.funded_peers:
            desc = peer.description or ""
            lines.append(f"| {peer.company_name} | {peer.round_type} | {peer.amount} | {peer.date} | {desc} |")
    else:
        lines.append("*No recent funding data found.*")
    lines.append("")

    lines.append("*Data sourced via Perplexity AI. May not be exhaustive.*")

    return "\n".join(lines)


def write_summary(summary: StructuredSummary, pdf_path: Path) -> Path:
    """Write summary to markdown file alongside PDF.

    Args:
        summary: StructuredSummary to write.
        pdf_path: Path to the PDF file (used to determine output path).

    Returns:
        Path to the created markdown file.
    """
    md_path = pdf_path.with_suffix(".md")
    content = format_markdown(summary)

    with open(md_path, "w") as f:
        f.write(content)

    return md_path


def summarize(api_key: str, screenshots: list[bytes]) -> StructuredSummary:
    """Generate structured summary from screenshots.

    Main entry point for summarization.

    Args:
        api_key: Perplexity API key.
        screenshots: List of PNG screenshot bytes.

    Returns:
        StructuredSummary with company analysis and peers.

    Raises:
        OCRError: If text extraction fails.
        SummaryError: If API call or parsing fails.
    """
    # Extract text from screenshots
    ocr_text = extract_text(screenshots)

    # Call Perplexity for analysis + peer search
    return call_perplexity(api_key, ocr_text)
