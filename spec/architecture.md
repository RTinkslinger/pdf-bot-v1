# Architecture Specification

## Document Info
- **Project**: DocSend to PDF Converter (topdf)
- **Version**: 1.1
- **Last Updated**: 2025-01-07
- **Changes**: Added Summarizer and Config components, updated exception hierarchy

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│                    (cli.py - Click framework)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator                                │
│                  (converter.py - Coordinates all modules)        │
└──────┬─────────────────┬─────────────────┬─────────────────────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Scraper    │  │  PDF Builder │  │    Name      │
│ (scraper.py) │  │(pdf_builder) │  │  Extractor   │
│              │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
       │
       ▼
┌──────────────┐
│   Auth       │
│   Handler    │
│  (auth.py)   │
└──────────────┘

[Optional: Post-Conversion Summarization]
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      CLI Layer (Summary Prompt)                   │
│              "Generate AI summary? [y/N]"                         │
└──────────────────────────┬───────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
       ┌──────────────┐          ┌──────────────┐
       │  Summarizer  │◀────────▶│   Config     │
       │(summarizer.py)│          │ (config.py)  │
       │  OCR + LLM   │          │  API Keys    │
       └──────────────┘          └──────────────┘
```

### 1.2 Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| CLI | `cli.py` | Parse arguments, invoke converter, display results, summary prompts |
| Orchestrator | `converter.py` | Coordinate scraper, builder, extractor |
| Scraper | `scraper.py` | Navigate DocSend, capture screenshots |
| Auth Handler | `auth.py` | Detect and handle authentication |
| PDF Builder | `pdf_builder.py` | Convert screenshots to PDF |
| Name Extractor | `name_extractor.py` | Extract company name |
| Exceptions | `exceptions.py` | Custom exception classes |
| Config | `config.py` | API key storage and retrieval |
| Summarizer | `summarizer.py` | OCR text extraction, LLM summarization |

---

## 2. Directory Structure

```
/Users/Aakash/pdfbot/
│
├── spec/                           # Specification documents
│   ├── SPEC.md                     # Full specification
│   ├── requirements.md             # Requirements
│   ├── architecture.md             # This document
│   └── test-plan.md               # Testing strategy
│
├── topdf/                          # Main package
│   ├── __init__.py                # Package init, version
│   ├── cli.py                     # Click CLI entry point
│   ├── converter.py               # Main orchestrator
│   ├── scraper.py                 # Playwright DocSend scraper
│   ├── auth.py                    # Authentication handlers
│   ├── pdf_builder.py             # Screenshot to PDF
│   ├── name_extractor.py          # Company name extraction
│   ├── config.py                  # API key management
│   ├── summarizer.py              # AI summarization (OCR + LLM)
│   └── exceptions.py              # Custom exceptions
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_cli.py
│   ├── test_scraper.py
│   ├── test_pdf_builder.py
│   ├── test_name_extractor.py
│   ├── test_auth.py
│   ├── test_config.py             # API key management tests
│   ├── test_summarizer.py         # Summarization tests
│   └── test_integration.py
│
├── converted PDFs/                 # Output directory
│   └── .gitkeep
│
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── setup.py                       # Package installation
├── pyproject.toml                # Modern Python config
├── .gitignore
└── README.md
```

---

## 3. Component Specifications

### 3.1 CLI Module (`cli.py`)

**Purpose**: Entry point for the application

**Interface**:
```python
@click.command()
@click.argument('url')
@click.option('--email', '-e', help='Email for protected documents')
@click.option('--passcode', '-p', help='Passcode for protected documents')
@click.option('--name', '-n', help='Override output filename')
@click.option('--output', '-o', default='converted PDFs', help='Output directory')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--version', is_flag=True, help='Show version')
def topdf(url, email, passcode, name, output, verbose, version):
    """Convert a DocSend link to PDF."""
```

**Dependencies**: click, rich, converter

### 3.2 Orchestrator (`converter.py`)

**Purpose**: Coordinates the conversion workflow

**Interface**:
```python
class Converter:
    def __init__(self, output_dir: str = 'converted PDFs'):
        pass

    async def convert(
        self,
        url: str,
        email: Optional[str] = None,
        passcode: Optional[str] = None,
        output_name: Optional[str] = None,
        verbose: bool = False
    ) -> ConversionResult:
        """
        Main conversion entry point.

        Returns:
            ConversionResult with pdf_path, company_name, page_count
        """
```

**Dependencies**: scraper, pdf_builder, name_extractor

### 3.3 Scraper Module (`scraper.py`)

**Purpose**: Navigate DocSend and capture page screenshots

**Interface**:
```python
class DocSendScraper:
    def __init__(self, headless: bool = True):
        pass

    async def scrape(
        self,
        url: str,
        email: Optional[str] = None,
        passcode: Optional[str] = None
    ) -> ScrapeResult:
        """
        Scrape DocSend document.

        Returns:
            ScrapeResult with screenshots, page_title, page_count
        """

    async def close(self):
        """Cleanup browser resources."""
```

**Internal Methods**:
| Method | Purpose |
|--------|---------|
| `_validate_url` | Verify DocSend URL format |
| `_launch_browser` | Start Playwright browser |
| `_navigate` | Go to URL with retry |
| `_detect_auth_type` | Check for email/passcode gate |
| `_handle_auth` | Fill authentication forms |
| `_get_page_count` | Extract total page count |
| `_capture_pages` | Screenshot each page |

### 3.4 Auth Handler (`auth.py`)

**Purpose**: Handle DocSend authentication flows

**Interface**:
```python
class AuthType(Enum):
    NONE = "none"
    EMAIL = "email"
    PASSCODE = "passcode"

class AuthHandler:
    async def detect_auth_type(self, page: Page) -> AuthType:
        """Detect which authentication is required."""

    async def handle_email_gate(
        self,
        page: Page,
        email: str
    ) -> bool:
        """Submit email form. Returns success."""

    async def handle_passcode_gate(
        self,
        page: Page,
        email: str,
        passcode: str
    ) -> bool:
        """Submit email + passcode. Returns success."""
```

### 3.5 PDF Builder (`pdf_builder.py`)

**Purpose**: Convert screenshots to PDF

**Interface**:
```python
class PDFBuilder:
    def build(self, screenshots: List[bytes]) -> bytes:
        """
        Convert list of PNG screenshots to PDF.

        Args:
            screenshots: List of PNG image bytes

        Returns:
            PDF file as bytes
        """

    def _normalize_dimensions(self, images: List[Image]) -> List[Image]:
        """Resize images to consistent dimensions."""

    def _optimize_images(self, images: List[Image]) -> List[bytes]:
        """Compress images for smaller PDF size."""
```

### 3.6 Name Extractor (`name_extractor.py`)

**Purpose**: Extract company name for filename

**Interface**:
```python
class NameExtractor:
    def extract(
        self,
        page_title: Optional[str],
        first_screenshot: Optional[bytes] = None
    ) -> str:
        """
        Extract company name using fallback chain:
        1. Parse page title
        2. OCR first slide
        3. Prompt user

        Returns:
            Sanitized company name
        """

    def _from_title(self, title: str) -> Optional[str]:
        """Parse company name from DocSend page title."""

    def _from_ocr(self, screenshot: bytes) -> Optional[str]:
        """Extract company name via OCR."""

    def _sanitize_filename(self, name: str) -> str:
        """Remove invalid filesystem characters."""

    def _prompt_user(self) -> str:
        """Ask user for company name."""
```

### 3.7 Exceptions (`exceptions.py`)

```python
class TopdfError(Exception):
    """Base exception for topdf."""

class InvalidURLError(TopdfError):
    """URL is not a valid DocSend link."""

class AuthenticationError(TopdfError):
    """Authentication failed."""

class ScrapingError(TopdfError):
    """Failed to scrape document."""

class PDFBuildError(TopdfError):
    """Failed to build PDF."""

class TimeoutError(TopdfError):
    """Operation timed out."""

class SummaryError(TopdfError):
    """Failed to generate summary."""

class OCRError(TopdfError):
    """Failed to extract text via OCR."""
```

### 3.8 Config Module (`config.py`)

**Purpose**: Manage API keys for LLM providers

**Interface**:
```python
CONFIG_PATH: Path = Path.home() / ".config" / "topdf" / "config.json"

def get_api_key(provider: str) -> Optional[str]:
    """Get API key from config file or environment variable.

    Lookup order:
    1. Config file (~/.config/topdf/config.json)
    2. Environment variable (ANTHROPIC_API_KEY or OPENAI_API_KEY)

    Returns:
        API key string or None if not found
    """

def save_api_key(provider: str, key: str) -> None:
    """Save API key to config file.

    Creates config directory if it doesn't exist.
    """

def clear_api_keys() -> None:
    """Remove all saved API keys."""

def has_api_key(provider: str) -> bool:
    """Check if API key exists in config or env."""

def get_masked_key(key: str) -> str:
    """Return masked version for display (e.g., sk-ant-****...****)."""
```

**Config File Format**:
```json
{
  "perplexity_api_key": "pplx-..."
}
```

### 3.9 Summarizer Module (`summarizer.py`)

**Purpose**: Extract text from screenshots and generate structured analysis with Perplexity

**Interface**:
```python
SECTORS = [
    "cybersecurity", "enterprise_tech", "consumer_tech", "consumer_goods",
    "fintech", "industrials", "robotics", "space_tech", "developer_tooling"
]

@dataclass
class CompanyAnalysis:
    company_name: str
    description: str  # ≤200 characters
    has_customers: bool
    customer_details: Optional[str]
    primary_sector: str
    secondary_sector: Optional[str]

@dataclass
class FundedPeer:
    company_name: str
    round_type: str  # "Seed", "Series A", etc.
    amount: str  # "$10M"
    date: str  # "Jan 2024"
    description: Optional[str]

@dataclass
class StructuredSummary:
    company: CompanyAnalysis
    funded_peers: list[FundedPeer]

class Summarizer:
    MAX_PAGES_TO_OCR: int = 5

    def __init__(self, perplexity_key: str) -> None:
        """Initialize with Perplexity API key."""

    def summarize(
        self,
        screenshots: list[bytes],
        company_name: str
    ) -> StructuredSummary:
        """
        Generate structured summary from screenshots using Perplexity.

        Pipeline:
        1. OCR first N pages using pytesseract
        2. Send text to Perplexity for analysis + peer search (single call)
        3. Parse response into StructuredSummary
        4. Return result

        Raises:
            OCRError: If text extraction fails
            SummaryError: If API call fails
        """

    @staticmethod
    def write_summary(result: StructuredSummary, pdf_path: Path) -> Path:
        """Write summary to markdown file alongside PDF.

        Returns:
            Path to the created .md file
        """
```

**Internal Methods**:
| Method | Purpose |
|--------|---------|
| `_check_tesseract` | Verify tesseract is installed |
| `_extract_text` | OCR screenshots to text |
| `_call_perplexity` | Single API call for analysis + peers |
| `_parse_response` | Parse Perplexity response to dataclasses |
| `_format_markdown` | Generate markdown output |

**Dependencies**: pytesseract, Pillow, openai (for Perplexity)

### 3.10 Perplexity Configuration

#### Provider and Model

| Provider | Model | Purpose |
|----------|-------|---------|
| Perplexity | sonar-pro | Deck analysis + funded peer search (single call) |

#### Combined Analysis + Peer Search Prompt

```
You are analyzing a pitch deck and researching the competitive landscape.

PITCH DECK CONTENT:
{ocr_text}

Please provide a structured analysis in the following JSON format:

{
  "company": {
    "company_name": "The company's name",
    "description": "What they do in exactly 200 characters or less",
    "has_customers": true/false,
    "customer_details": "Names/logos of customers if mentioned, else null",
    "primary_sector": "One of: cybersecurity, enterprise_tech, consumer_tech, consumer_goods, fintech, industrials, robotics, space_tech, developer_tooling",
    "secondary_sector": "Second most relevant sector or null"
  },
  "funded_peers": [
    {
      "company_name": "Competitor name",
      "round_type": "Seed/Series A/Series B",
      "amount": "$XM",
      "date": "Mon YYYY",
      "description": "One sentence description"
    }
  ]
}

INSTRUCTIONS:
1. Analyze the pitch deck content to extract company information
2. Search for up to 10 similar companies that raised Seed, Series A, or Series B rounds in the last 24 months
3. description must be ≤200 characters
4. primary_sector MUST be from the allowed list
5. Return valid JSON only
```

#### Perplexity API Setup

```python
from openai import OpenAI

perplexity = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)

response = perplexity.chat.completions.create(
    model="sonar-pro",
    messages=[{"role": "user", "content": prompt}]
)
```

#### Allowed Sector Tags

```python
SECTORS = [
    "cybersecurity",
    "enterprise_tech",
    "consumer_tech",
    "consumer_goods",
    "fintech",
    "industrials",
    "robotics",
    "space_tech",
    "developer_tooling"
]
```

### 3.11 Summarization Error Handling

| Scenario | Exception | User Message | Behavior |
|----------|-----------|--------------|----------|
| Tesseract not installed | `OCRError` | "Tesseract not found. Install with: brew install tesseract" | Skip summary |
| No text extracted | `OCRError` | "Could not extract text from document" | Skip summary |
| Missing Perplexity key | `SummaryError` | "Perplexity API key required for summarization" | Prompt for key |
| Invalid API key | `SummaryError` | "Invalid API key. Please check and try again" | Skip summary |
| Perplexity API failure | `SummaryError` | "Could not generate summary" | Skip summary |
| Invalid JSON response | `SummaryError` | "Failed to parse response" | Retry once, then skip |

#### Graceful Degradation

Summary failures must NOT affect PDF conversion:

```python
try:
    # OCR + Perplexity analysis (single call)
    result = await self._call_perplexity(text)
    self.write_summary(result, pdf_path)
except (SummaryError, OCRError) as e:
    console.print(f"[yellow]Warning: Could not generate summary - {e}[/yellow]")
    # PDF already saved, continue without summary
```

---

## 4. Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ INPUT: topdf https://docsend.com/view/abc123 -e user@email.com      │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: URL Validation                                               │
│   └─→ Regex: ^https?://(www\.)?docsend\.com/view/[\w-]+             │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Browser Launch                                               │
│   └─→ Playwright Chromium (headless)                                 │
│   └─→ Viewport: 1920x1080                                           │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Navigate to URL                                              │
│   └─→ page.goto(url, wait_until='networkidle')                      │
│   └─→ Timeout: 30 seconds                                           │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Auth Detection & Handling                                    │
│   └─→ Detect: email gate or passcode gate                           │
│   └─→ If auth required: fill form, submit, wait                     │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Page Enumeration                                             │
│   └─→ Find: pagination element                                       │
│   └─→ Extract: total page count (e.g., "1 of 24")                   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: Screenshot Capture Loop                                      │
│   └─→ For page in range(1, total_pages + 1):                        │
│       └─→ Navigate to page                                          │
│       └─→ Wait for render                                           │
│       └─→ Capture screenshot (PNG)                                  │
│       └─→ Add to screenshots[]                                      │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: Name Extraction                                              │
│   └─→ Try: parse page.title() → "Company X | DocSend"               │
│   └─→ Fallback: OCR on first screenshot                             │
│   └─→ Final: prompt user                                            │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 8: PDF Assembly                                                 │
│   └─→ Load screenshots as PIL Images                                │
│   └─→ Normalize dimensions                                          │
│   └─→ Convert to PDF with img2pdf                                   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 9: Save PDF                                                     │
│   └─→ Path: "converted PDFs/{company_name}.pdf"                     │
│   └─→ Handle duplicates: append (1), (2), etc.                      │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 10: Cleanup                                                     │
│   └─→ Close browser                                                 │
│   └─→ Delete temp files                                             │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ OUTPUT: /Users/Aakash/pdfbot/converted PDFs/Company X.pdf            │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.1 Summarization Data Flow (Optional)

After PDF conversion completes, the user is prompted for optional AI summarization:

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: User Prompt                                                  │
│   └─→ "Generate AI summary? [y/N]"                                  │
│   └─→ If 'n', skip to end                                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: API Key Resolution                                           │
│   └─→ Check: ~/.config/topdf/config.json                            │
│   └─→ Check: ENV (PERPLEXITY_API_KEY)                               │
│   └─→ If missing: Prompt "Enter your Perplexity API key: ****"      │
│   └─→ Offer: "Save for future use? [y/N]"                           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Text Extraction (OCR)                                        │
│   └─→ Load first 5 screenshots from conversion result               │
│   └─→ pytesseract.image_to_string() on each                        │
│   └─→ Combine into single text block                                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Perplexity Analysis (Single Call)                            │
│   └─→ Send OCR text + analysis prompt to Perplexity API            │
│   └─→ Perplexity analyzes deck AND searches for funded peers       │
│   └─→ Parse JSON response: company + funded_peers                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Write Markdown                                               │
│   └─→ Path: "converted PDFs/{company_name}.md"                      │
│   └─→ Content: Structured summary with peers table                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ OUTPUT: Summary saved to converted PDFs/Company X.md                 │
└─────────────────────────────────────────────────────────────────────┘
```

#### Output Markdown Format

```markdown
# {Company Name}

## Overview
{200 character description of what they do}

## Traction
**Early Customers:** Yes/No
{Details if mentioned: customer names, logos, case studies}

## Sector
**Primary:** {sector}
**Secondary:** {sector or N/A}

## Funded Peers (24-month lookback)
| Company | Round | Amount | Date | Description |
|---------|-------|--------|------|-------------|
| Peer 1  | Series A | $10M | Jan 2024 | Brief description |
| ... up to 10 peers ... |

*Data sourced via Perplexity AI. May not be exhaustive.*
```

---

## 5. Sequence Diagram

```
User          CLI           Converter       Scraper         PDFBuilder    NameExtractor
  │            │               │               │                │              │
  │──topdf url─▶               │               │                │              │
  │            │──convert()───▶│               │                │              │
  │            │               │──scrape()────▶│                │              │
  │            │               │               │──launch()      │              │
  │            │               │               │──navigate()    │              │
  │            │               │               │──detect_auth() │              │
  │            │               │               │──handle_auth() │              │
  │            │               │               │──capture_pages()              │
  │            │               │◀──screenshots─│                │              │
  │            │               │               │                │              │
  │            │               │──────────────extract()────────▶│              │
  │            │               │◀─────────────company_name──────│              │
  │            │               │                                │              │
  │            │               │───────build()─▶│               │              │
  │            │               │◀──────pdf─────│               │              │
  │            │               │                                │              │
  │            │               │──save_pdf()   │               │              │
  │            │◀──result──────│               │               │              │
  │◀──success──│               │               │               │              │
```

---

## 6. Error Handling Strategy

### Exception Hierarchy
```
TopdfError (base)
├── InvalidURLError
├── AuthenticationError
│   ├── EmailRequiredError
│   └── PasscodeRequiredError
├── ScrapingError
│   ├── PageLoadError
│   └── ScreenshotError
├── PDFBuildError
├── TimeoutError
├── SummaryError
│   ├── APIKeyError
│   └── LLMError
└── OCRError
```

### Retry Policy
| Operation | Max Retries | Backoff |
|-----------|-------------|---------|
| Page navigation | 3 | Exponential (1s, 2s, 4s) |
| Screenshot capture | 3 | Linear (1s each) |
| Auth form submit | 1 | None |

### Error Messages
All errors should include:
1. What went wrong
2. Possible cause
3. Suggested action

Example:
```
Error: Failed to load DocSend page
Cause: Network timeout after 30 seconds
Action: Check your internet connection and try again
```

---

## 7. Security Considerations

### Data Handling
- No document content logged
- No URLs logged
- DocSend credentials never persisted
- Core PDF processing local
- Document text only sent to LLM if user explicitly opts in

### API Key Security
- Keys stored in user home directory (`~/.config/topdf/`)
- Standard file permissions (user read/write only)
- Keys never logged or displayed in full
- Masked display format: `sk-ant-****...****`
- Privacy message shown when saving: "Key saved locally... (not sent anywhere except to the LLM API)"
- No telemetry or external transmission of keys (except to chosen LLM)

### Browser Security
- Headless mode (no visual UI)
- Isolated browser context
- Clean up on exit

### Input Validation
- URL format validated
- Email format validated (basic)
- Path traversal prevented
- API key format validated (basic prefix check)

---

## 8. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| 20-page conversion | <60 seconds | End-to-end time |
| Memory usage | <500MB | Peak during conversion |
| PDF size | <5MB per 20 pages | Output file size |
| Browser startup | <5 seconds | First page load |
