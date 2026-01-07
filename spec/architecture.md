# Architecture Specification

## Document Info
- **Project**: DocSend to PDF Converter (topdf)
- **Version**: 1.0
- **Last Updated**: 2025-01-07

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
```

### 1.2 Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| CLI | `cli.py` | Parse arguments, invoke converter, display results |
| Orchestrator | `converter.py` | Coordinate scraper, builder, extractor |
| Scraper | `scraper.py` | Navigate DocSend, capture screenshots |
| Auth Handler | `auth.py` | Detect and handle authentication |
| PDF Builder | `pdf_builder.py` | Convert screenshots to PDF |
| Name Extractor | `name_extractor.py` | Extract company name |
| Exceptions | `exceptions.py` | Custom exception classes |
| Config | `config.py` | Configuration management |

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
│   ├── config.py                  # Configuration management
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
└── TimeoutError
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
- Credentials never persisted
- All processing local

### Browser Security
- Headless mode (no visual UI)
- Isolated browser context
- Clean up on exit

### Input Validation
- URL format validated
- Email format validated (basic)
- Path traversal prevented

---

## 8. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| 20-page conversion | <60 seconds | End-to-end time |
| Memory usage | <500MB | Peak during conversion |
| PDF size | <5MB per 20 pages | Output file size |
| Browser startup | <5 seconds | First page load |
