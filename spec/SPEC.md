# DocSend to PDF Converter - Comprehensive Specification

## Table of Contents
1. [Requirements](#1-requirements)
2. [Design Approach](#2-design-approach)
3. [Implementation Options](#3-implementation-options)
4. [Recommended Implementation](#4-recommended-implementation)
5. [Technology Architecture](#5-technology-architecture)
6. [Phased Build & Deploy Plan](#6-phased-build--deploy-plan)
7. [Testing Strategy](#7-testing-strategy)

---

# 1. Requirements

## 1.1 Functional Requirements

### FR-1: Core Conversion
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Accept DocSend URL as input via CLI command `topdf <url>` | Must Have |
| FR-1.2 | Convert DocSend document to PDF format | Must Have |
| FR-1.3 | Support multi-page documents (pitch decks typically 10-30 pages) | Must Have |
| FR-1.4 | Preserve visual fidelity of original document | Must Have |
| FR-1.5 | Generate searchable PDF with text layer (OCR) | Nice to Have |

### FR-2: Authentication Handling
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Support open/public DocSend links | Must Have |
| FR-2.2 | Support email-gated DocSend links | Must Have |
| FR-2.3 | Support passcode-protected DocSend links | Must Have |
| FR-2.4 | Prompt user for credentials when required | Must Have |
| FR-2.5 | Accept credentials via CLI flags (`--email`, `--passcode`) | Should Have |

### FR-3: File Naming & Organization
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Automatically extract company name from document | Must Have |
| FR-3.2 | Save PDF with company name as filename | Must Have |
| FR-3.3 | Store converted PDFs in `converted PDFs/` folder | Must Have |
| FR-3.4 | Allow manual override of filename via `--name` flag | Should Have |
| FR-3.5 | Handle filename conflicts (append number or timestamp) | Should Have |

### FR-4: User Experience
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Show progress indicator during conversion | Should Have |
| FR-4.2 | Display success message with output file path | Must Have |
| FR-4.3 | Provide clear error messages for failures | Must Have |
| FR-4.4 | Support `--help` flag with usage documentation | Must Have |

### FR-5: AI Summarization (Optional)
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | Prompt for AI summary after PDF conversion | Should Have |
| FR-5.2 | Extract text from screenshots using OCR | Should Have |
| FR-5.3 | Generate structured analysis via Perplexity (single call) | Should Have |
| FR-5.4 | Generate ≤200 character company description | Should Have |
| FR-5.5 | Assign sector tags (primary + secondary) | Should Have |
| FR-5.6 | Identify early customer traction | Should Have |
| FR-5.7 | Find recently funded peers (up to 10) | Should Have |
| FR-5.8 | Save summary as markdown file alongside PDF | Should Have |
| FR-5.9 | Summary failure must not break PDF conversion | Must Have |

### FR-6: API Key Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | Store Perplexity API key in `~/.config/topdf/config.json` | Should Have |
| FR-6.2 | Support API key via environment variable (PERPLEXITY_API_KEY) | Should Have |
| FR-6.3 | Prompt for API key if not configured | Should Have |
| FR-6.4 | Offer to save key after manual entry | Should Have |
| FR-6.5 | Support `--check-key` and `--reset-key` flags | Should Have |

## 1.2 Non-Functional Requirements

### NFR-1: Privacy & Security
| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-1.1 | Core PDF conversion must happen locally | Must Have |
| NFR-1.2 | Document data only sent to LLM if user opts in | Must Have |
| NFR-1.3 | No logging of document content or URLs | Must Have |
| NFR-1.4 | API keys stored locally only | Should Have |
| NFR-1.5 | API keys never logged or displayed in full | Should Have |

### NFR-2: Performance
| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-2.1 | Convert typical 20-page deck in under 60 seconds | Should Have |
| NFR-2.2 | Minimal memory footprint (< 500MB RAM) | Should Have |

### NFR-3: Reliability
| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-3.1 | Handle network timeouts gracefully | Should Have |
| NFR-3.2 | Retry failed page captures (max 3 attempts) | Should Have |
| NFR-3.3 | Produce valid PDF even if OCR fails | Must Have |

### NFR-4: Maintainability
| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-4.1 | Modular code architecture for easy updates | Should Have |
| NFR-4.2 | Handle DocSend UI changes with minimal code changes | Should Have |

## 1.3 Constraints

- **Platform**: macOS (primary), with potential Linux support
- **Python Version**: 3.9+
- **System Dependency**: Tesseract OCR must be installed
- **Network**: Requires internet access to fetch DocSend documents

---

# 2. Design Approach

## 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│                    (cli.py - Click framework)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator                                │
│                  (Coordinates all modules)                       │
└──────┬─────────────────┬─────────────────┬─────────────────────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Scraper    │  │  PDF Builder │  │    Name      │
│ (Playwright) │  │ (img2pdf)    │  │  Extractor   │
│              │  │              │  │  (OCR)       │
└──────────────┘  └──────────────┘  └──────────────┘
       │
       ▼
┌──────────────┐
│   Auth       │
│   Handler    │
└──────────────┘

[Optional: Post-Conversion Summarization]
                           │
                           ▼
       ┌──────────────┐          ┌──────────────┐
       │  Summarizer  │◀────────▶│   Config     │
       │(summarizer.py)│          │ (config.py)  │
       │  OCR + LLM   │          │  API Keys    │
       └──────────────┘          └──────────────┘
```

## 2.2 Core Design Decisions

### Decision 1: Headless Browser vs API
**Choice**: Headless browser (Playwright)
**Rationale**: DocSend renders documents client-side; no public API for PDF export

### Decision 2: Screenshot Capture vs DOM Extraction
**Choice**: Screenshot capture
**Rationale**: Preserves exact visual fidelity; handles complex layouts/animations

### Decision 3: Company Name Extraction Strategy
**Choice**: Multi-source with fallback chain
1. DocSend page title (most reliable)
2. First slide OCR (fallback)
3. Manual input prompt (final fallback)

---

# 3. Implementation Options

## Option A: Browser Automation (Playwright/Python)

### Description
Use Playwright to control a headless Chromium browser, navigate to DocSend, capture screenshots of each page, and combine into PDF.

### Technical Approach
```python
# Pseudocode
async def convert_docsend(url):
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(url)

    # Handle auth if needed
    if await page.query_selector('.email-gate'):
        await handle_auth(page)

    # Capture each page
    screenshots = []
    total_pages = await get_page_count(page)
    for i in range(total_pages):
        await navigate_to_page(page, i)
        screenshot = await page.screenshot()
        screenshots.append(screenshot)

    # Build PDF
    pdf = create_pdf(screenshots)
    return pdf
```

### Pros
| Advantage | Details |
|-----------|---------|
| Full privacy | All processing local, no external APIs |
| Complete control | Handle any auth scenario |
| Free | No API costs |
| Reliable | You maintain it, no service dependency |
| Flexible | Can adapt to DocSend UI changes |

### Cons
| Disadvantage | Details |
|--------------|---------|
| Complex | 300-500 lines of code |
| Slow | 15-45 seconds per document |
| Resource heavy | Headless browser uses ~200-400MB RAM |
| Brittle | DocSend UI changes may break selectors |
| Setup required | Playwright browser installation |

### Effort Estimate
- Development: 2-3 days
- Testing: 1-2 days
- Total: 3-5 days

---

## Option B: Third-Party API (docsend2pdf.com)

### Description
Use the docsend2pdf.com API to convert documents via simple HTTP POST request.

### Technical Approach
```python
import requests

def convert_docsend(url):
    response = requests.post(
        'https://docsend2pdf.com/api/convert',
        json={'url': url}
    )
    return response.content  # PDF bytes
```

### Pros
| Advantage | Details |
|-----------|---------|
| Simple | ~50 lines of code |
| Fast to build | Working prototype in 1 hour |
| Fast conversion | 2-5 seconds |
| Maintained by others | No scraper maintenance |

### Cons
| Disadvantage | Details |
|--------------|---------|
| **Privacy risk** | DocSend URLs sent to third-party |
| Cost | May require payment for heavy use |
| Service dependency | Could shut down or change |
| Limited auth support | May not handle passcodes |
| Rate limits | Unknown restrictions |

### Effort Estimate
- Development: 0.5 days
- Testing: 0.5 days
- Total: 1 day

### **NOT RECOMMENDED** for investor use due to privacy concerns.

---

## Option C: Open-Source Scraper (docsend_scraper)

### Description
Leverage existing open-source Python library that already handles DocSend scraping.

### Technical Approach
```python
from docsend_scraper import DocSendScraper

def convert_docsend(url, email=None, passcode=None):
    scraper = DocSendScraper()
    pdf_path = scraper.download(url, email=email, passcode=passcode)
    return pdf_path
```

### Pros
| Advantage | Details |
|-----------|---------|
| Pre-built | Core logic already implemented |
| Open source | Can inspect and modify |
| Local processing | Privacy preserved |
| Docker support | Easy deployment |

### Cons
| Disadvantage | Details |
|--------------|---------|
| Maintenance unknown | May be outdated |
| Less flexible | Limited customization |
| Dependency risk | Library could be abandoned |
| May not work | DocSend may have changed since last update |

### Effort Estimate
- Development: 1 day
- Testing: 1 day
- Total: 2 days (if it works)

---

## Option Comparison Matrix

| Criteria | Weight | Option A (Playwright) | Option B (API) | Option C (OSS) |
|----------|--------|----------------------|----------------|----------------|
| Privacy | 30% | 10 | 2 | 10 |
| Reliability | 25% | 8 | 7 | 5 |
| Ease of Build | 15% | 5 | 10 | 7 |
| Maintainability | 15% | 7 | 3 | 4 |
| Performance | 10% | 5 | 9 | 6 |
| Cost | 5% | 10 | 5 | 10 |
| **Weighted Score** | 100% | **7.65** | 5.25 | 6.85 |

---

# 4. Recommended Implementation

## Recommendation: Option A - Browser Automation with Playwright

### Justification

1. **Privacy is non-negotiable**: As an investor reviewing confidential pitch decks, sending URLs to third-party services is unacceptable. Founders would not consent to this.

2. **Full control over authentication**: Mixed auth scenarios (some open, some protected) require flexibility that only browser automation provides.

3. **Long-term reliability**: You own and control the code. No risk of service shutdown or pricing changes.

4. **Customizable name extraction**: Can tune heuristics specifically for pitch deck formats (company names typically appear in title slide).

### Implementation Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| Browser Control | Playwright | Navigate, interact, screenshot |
| PDF Generation | img2pdf | Combine images into PDF |
| OCR | pytesseract + Tesseract | Extract text for naming |
| CLI | Click | User interface |
| Image Processing | Pillow | Resize, optimize screenshots |

---

# 5. Technology Architecture

## 5.1 System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                              USER                                       │
│                                                                         │
│   $ topdf https://docsend.com/view/abc123 --email investor@fund.com    │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         CLI LAYER (cli.py)                              │
│                                                                         │
│  • Parse arguments (url, email, passcode, name, output)                │
│  • Validate URL format                                                  │
│  • Initialize progress display                                          │
│  • Call orchestrator                                                    │
│  • Display result                                                       │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR (converter.py)                         │
│                                                                         │
│  async def convert(url, email, passcode, output_name):                 │
│      1. scraper.scrape(url, email, passcode) → screenshots[]           │
│      2. name_extractor.extract(screenshots, page_title) → company_name │
│      3. pdf_builder.build(screenshots) → pdf_bytes                     │
│      4. save_pdf(pdf_bytes, company_name, output_dir)                  │
│      5. return result                                                   │
└───────┬──────────────────────┬──────────────────────┬──────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   SCRAPER     │      │  PDF BUILDER  │      │NAME EXTRACTOR │
│ (scraper.py)  │      │(pdf_builder.py│      │(name_extract. │
│               │      │               │      │      py)      │
│ • Launch      │      │ • Take image  │      │ • Parse page  │
│   browser     │      │   list        │      │   title       │
│ • Navigate    │      │ • Resize to   │      │ • OCR first   │
│   to URL      │      │   consistent  │      │   slide       │
│ • Detect auth │      │   dimensions  │      │ • Apply       │
│ • Fill forms  │      │ • Convert to  │      │   heuristics  │
│ • Capture     │      │   PDF pages   │      │ • Fallback    │
│   pages       │      │ • Combine     │      │   to manual   │
│ • Return      │      │   into single │      │ • Sanitize    │
│   screenshots │      │   PDF         │      │   filename    │
└───────┬───────┘      └───────────────┘      └───────────────┘
        │
        ▼
┌───────────────┐
│ AUTH HANDLER  │
│(auth.py)      │
│               │
│ • Detect gate │
│   type        │
│ • Email form  │
│ • Passcode    │
│   form        │
│ • Wait for    │
│   access      │
└───────────────┘
```

## 5.2 Component Specifications

### 5.2.1 CLI Module (`cli.py`)

```python
@click.command()
@click.argument('url')
@click.option('--email', '-e', help='Email for protected documents')
@click.option('--passcode', '-p', help='Passcode for protected documents')
@click.option('--name', '-n', help='Override output filename')
@click.option('--output', '-o', default='converted PDFs', help='Output directory')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def topdf(url, email, passcode, name, output, verbose):
    """Convert a DocSend link to PDF."""
    pass
```

### 5.2.2 Scraper Module (`scraper.py`)

**Class: `DocSendScraper`**

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `__init__` | headless: bool | None | Initialize Playwright |
| `scrape` | url, email?, passcode? | List[bytes] | Main conversion method |
| `_detect_auth_type` | page | AuthType enum | Check for email/passcode gate |
| `_handle_email_gate` | page, email | None | Fill email form |
| `_handle_passcode_gate` | page, email, passcode | None | Fill passcode form |
| `_get_page_count` | page | int | Determine total pages |
| `_navigate_to_page` | page, index | None | Go to specific page |
| `_capture_page` | page | bytes | Screenshot current page |
| `close` | None | None | Cleanup browser |

### 5.2.3 PDF Builder Module (`pdf_builder.py`)

**Class: `PDFBuilder`**

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `build` | screenshots: List[bytes] | bytes | Convert images to PDF |
| `_normalize_dimensions` | images | List[Image] | Resize to consistent size |
| `_optimize_images` | images | List[bytes] | Compress for smaller PDF |

### 5.2.4 Name Extractor Module (`name_extractor.py`)

**Class: `NameExtractor`**

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `extract` | page_title, first_screenshot | str | Get company name |
| `_from_title` | title | str? | Parse DocSend page title |
| `_from_ocr` | screenshot | str? | OCR first slide |
| `_sanitize_filename` | name | str | Remove invalid chars |
| `_prompt_user` | None | str | Ask user for name |

### 5.2.5 Converter Module Modifications

For summarization support, the `ConversionResult` dataclass includes screenshots:

```python
@dataclass
class ConversionResult:
    pdf_path: Path
    company_name: str
    page_count: int
    screenshots: list[bytes]  # Added for summarization
```

## 5.3 Data Flow

```
Input: https://docsend.com/view/abc123

Step 1: URL Validation
  └─→ Regex match: ^https?://(www\.)?docsend\.com/view/[\w-]+

Step 2: Browser Launch
  └─→ Playwright Chromium (headless mode)
  └─→ Set viewport: 1920x1080

Step 3: Navigation
  └─→ page.goto(url, wait_until='networkidle')
  └─→ Timeout: 30 seconds

Step 4: Auth Detection
  └─→ Check for selector: '[data-testid="email-gate"]'
  └─→ Check for selector: '[data-testid="passcode-input"]'
  └─→ If found, handle auth flow

Step 5: Page Enumeration
  └─→ Find pagination element
  └─→ Extract total page count (e.g., "1 of 24")

Step 6: Screenshot Capture Loop
  └─→ For each page (1 to N):
      └─→ Click next/navigate
      └─→ Wait for render (networkidle)
      └─→ page.screenshot(type='png', full_page=False)
      └─→ Append to screenshots[]

Step 7: Title Extraction
  └─→ page.title() → "Company X - Series A Pitch Deck | DocSend"
  └─→ Parse: "Company X"

Step 8: PDF Assembly
  └─→ Load screenshots as PIL Images
  └─→ Normalize to consistent dimensions
  └─→ Convert to PDF using img2pdf
  └─→ Output: bytes

Step 9: Save
  └─→ Path: "converted PDFs/Company X.pdf"
  └─→ Handle conflicts: "Company X (1).pdf"

Step 10: Cleanup
  └─→ Close browser
  └─→ Delete temp files

Output: /Users/Aakash/pdfbot/converted PDFs/Company X.pdf
```

## 5.4 Directory Structure

```
/Users/Aakash/pdfbot/
│
├── spec/                           # Specification documents
│   ├── SPEC.md                     # This document
│   ├── requirements.md             # Detailed requirements
│   ├── architecture.md             # Architecture diagrams
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

## 5.5 Dependencies

### Production Dependencies (`requirements.txt`)
```
playwright>=1.40.0
Pillow>=10.0.0
img2pdf>=0.5.0
pytesseract>=0.3.10
click>=8.1.0
rich>=13.0.0        # For progress bars and pretty output
```

### Development Dependencies (`requirements-dev.txt`)
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.5.0
```

### System Dependencies
```bash
# macOS
brew install tesseract

# After pip install
playwright install chromium
```

### Optional Dependencies (Summarization)
```
openai>=1.0.0          # Perplexity API (uses OpenAI-compatible SDK)
```

**Installation:** `pip install topdf[summarize]`

**Note:** Perplexity API uses the OpenAI SDK with `base_url="https://api.perplexity.ai"`

---

# 6. Phased Build & Deploy Plan

## Phase 1: Project Foundation
**Goal**: Set up project structure and basic CLI

### Tasks
- [ ] 1.1 Create directory structure (`pdfbot/`, `topdf/`, `tests/`, `spec/`)
- [ ] 1.2 Create `requirements.txt` with all dependencies
- [ ] 1.3 Create `setup.py` for package installation
- [ ] 1.4 Create `pyproject.toml` with tool configurations
- [ ] 1.5 Create `.gitignore`
- [ ] 1.6 Create `topdf/__init__.py` with version
- [ ] 1.7 Create basic `cli.py` with argument parsing
- [ ] 1.8 Create `exceptions.py` with custom exceptions
- [ ] 1.9 Install dependencies and Playwright browsers
- [ ] 1.10 Verify `topdf --help` works

### Testing for Phase 1
```bash
# Test 1.1: Directory structure exists
ls -la pdfbot/topdf/
ls -la pdfbot/tests/

# Test 1.2: Dependencies install
pip install -r requirements.txt

# Test 1.3: Package installs
pip install -e .

# Test 1.4: CLI responds
topdf --help

# Test 1.5: Playwright installed
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### Exit Criteria
- [ ] All directories created
- [ ] `pip install -e .` succeeds
- [ ] `topdf --help` shows usage
- [ ] All tests pass

---

## Phase 2: Core Scraper (No Auth)
**Goal**: Scrape and capture pages from open DocSend links

### Tasks
- [ ] 2.1 Create `scraper.py` with `DocSendScraper` class
- [ ] 2.2 Implement browser launch/close
- [ ] 2.3 Implement URL navigation with error handling
- [ ] 2.4 Implement page count detection
- [ ] 2.5 Implement page navigation (next/prev)
- [ ] 2.6 Implement screenshot capture
- [ ] 2.7 Add retry logic for failed captures
- [ ] 2.8 Add timeout handling
- [ ] 2.9 Write unit tests for scraper
- [ ] 2.10 Manual test with real open DocSend link

### Testing for Phase 2
```bash
# Unit tests
pytest tests/test_scraper.py -v

# Integration test (requires real DocSend URL)
python -c "
from topdf.scraper import DocSendScraper
scraper = DocSendScraper()
screenshots = scraper.scrape('https://docsend.com/view/REAL_OPEN_LINK')
print(f'Captured {len(screenshots)} pages')
scraper.close()
"

# Verify screenshots are valid PNGs
file /tmp/test_screenshot_*.png
```

### Exit Criteria
- [ ] Scraper captures all pages from open DocSend
- [ ] Screenshots are valid PNG images
- [ ] Retry logic handles transient failures
- [ ] Unit tests pass with >80% coverage

---

## Phase 3: Authentication Handling
**Goal**: Support email and passcode protected documents

### Tasks
- [ ] 3.1 Create `auth.py` module
- [ ] 3.2 Implement auth type detection
- [ ] 3.3 Implement email gate handler
- [ ] 3.4 Implement passcode gate handler
- [ ] 3.5 Add CLI prompts for credentials
- [ ] 3.6 Integrate auth into scraper flow
- [ ] 3.7 Handle auth failures gracefully
- [ ] 3.8 Write unit tests for auth module
- [ ] 3.9 Manual test with email-protected DocSend
- [ ] 3.10 Manual test with passcode-protected DocSend

### Testing for Phase 3
```bash
# Unit tests
pytest tests/test_auth.py -v

# Integration test - email protected
topdf https://docsend.com/view/EMAIL_PROTECTED --email test@example.com

# Integration test - passcode protected
topdf https://docsend.com/view/PASSCODE_PROTECTED -e test@example.com -p secret123

# Test auth failure handling
topdf https://docsend.com/view/PROTECTED --email wrong@email.com
# Should show clear error message
```

### Exit Criteria
- [ ] Email-gated documents accessible with valid email
- [ ] Passcode-protected documents accessible with valid credentials
- [ ] Clear error messages for invalid credentials
- [ ] CLI prompts work when credentials not provided

---

## Phase 4: PDF Builder
**Goal**: Convert screenshots to single PDF file

### Tasks
- [ ] 4.1 Create `pdf_builder.py` module
- [ ] 4.2 Implement image loading from bytes
- [ ] 4.3 Implement dimension normalization
- [ ] 4.4 Implement PDF creation with img2pdf
- [ ] 4.5 Implement image compression/optimization
- [ ] 4.6 Handle edge cases (single page, large images)
- [ ] 4.7 Write unit tests
- [ ] 4.8 Verify PDF opens correctly in Preview/Acrobat

### Testing for Phase 4
```bash
# Unit tests
pytest tests/test_pdf_builder.py -v

# Integration test
python -c "
from topdf.pdf_builder import PDFBuilder
from pathlib import Path

# Load test images
screenshots = [Path(f'test_page_{i}.png').read_bytes() for i in range(3)]
builder = PDFBuilder()
pdf_bytes = builder.build(screenshots)
Path('test_output.pdf').write_bytes(pdf_bytes)
print('PDF created successfully')
"

# Verify PDF
open test_output.pdf  # Should open in Preview
pdfinfo test_output.pdf  # Check metadata
```

### Exit Criteria
- [ ] PDF contains all pages in correct order
- [ ] PDF opens without errors in standard viewers
- [ ] File size is reasonable (not bloated)
- [ ] Unit tests pass

---

## Phase 5: Company Name Extraction
**Goal**: Automatically name PDFs based on company name

### Tasks
- [ ] 5.1 Create `name_extractor.py` module
- [ ] 5.2 Implement title parsing (DocSend page title)
- [ ] 5.3 Implement OCR-based extraction (pytesseract)
- [ ] 5.4 Implement fallback chain logic
- [ ] 5.5 Implement filename sanitization
- [ ] 5.6 Add user prompt for manual input
- [ ] 5.7 Handle duplicate filenames
- [ ] 5.8 Write unit tests
- [ ] 5.9 Test with various real pitch deck names

### Testing for Phase 5
```bash
# Unit tests
pytest tests/test_name_extractor.py -v

# Test title parsing
python -c "
from topdf.name_extractor import NameExtractor
extractor = NameExtractor()

# Test various title formats
titles = [
    'Acme Corp - Pitch Deck | DocSend',
    'Series A - Startup Inc | DocSend',
    'Company XYZ',
]
for title in titles:
    name = extractor._from_title(title)
    print(f'{title!r} → {name!r}')
"

# Test filename sanitization
python -c "
from topdf.name_extractor import NameExtractor
extractor = NameExtractor()
dirty_names = ['Company/Inc', 'Startup: AI', 'Name\\With\\Slashes']
for name in dirty_names:
    clean = extractor._sanitize_filename(name)
    print(f'{name!r} → {clean!r}')
"
```

### Exit Criteria
- [ ] Title parsing extracts company name correctly
- [ ] OCR fallback works when title unavailable
- [ ] Filenames are valid for filesystem
- [ ] Duplicates handled with numbering

---

## Phase 6: Full Integration
**Goal**: Connect all components into working CLI tool

### Tasks
- [ ] 6.1 Create `converter.py` orchestrator
- [ ] 6.2 Wire CLI to orchestrator
- [ ] 6.3 Add progress indicators (rich library)
- [ ] 6.4 Add verbose output mode
- [ ] 6.5 Create output directory if not exists
- [ ] 6.6 Implement full error handling
- [ ] 6.7 Write integration tests
- [ ] 6.8 End-to-end test with various DocSend types
- [ ] 6.9 Performance optimization
- [ ] 6.10 Final manual testing

### Testing for Phase 6
```bash
# Integration tests
pytest tests/test_integration.py -v

# End-to-end tests (manual)
# Test 1: Open document
topdf https://docsend.com/view/OPEN_LINK
ls -la "converted PDFs/"

# Test 2: Email protected
topdf https://docsend.com/view/EMAIL_LINK -e investor@fund.com

# Test 3: Passcode protected
topdf https://docsend.com/view/PASSCODE_LINK -e investor@fund.com -p secret

# Test 4: Custom name
topdf https://docsend.com/view/LINK --name "Custom Name Here"

# Test 5: Custom output directory
topdf https://docsend.com/view/LINK -o ~/Desktop/decks

# Test 6: Verbose mode
topdf https://docsend.com/view/LINK -v

# Performance test
time topdf https://docsend.com/view/LINK
# Should complete in <60 seconds
```

### Exit Criteria
- [ ] Full workflow works end-to-end
- [ ] Progress bar shows during conversion
- [ ] All CLI options work as documented
- [ ] Error messages are helpful
- [ ] Performance meets requirements (<60s)

---

## Phase 7: Polish & Documentation
**Goal**: Production-ready release

### Tasks
- [ ] 7.1 Create comprehensive README.md
- [ ] 7.2 Add installation instructions
- [ ] 7.3 Add usage examples
- [ ] 7.4 Add troubleshooting section
- [ ] 7.5 Create shell alias suggestion (`alias topdf='python -m topdf'`)
- [ ] 7.6 Add `--version` flag
- [ ] 7.7 Final code review and cleanup
- [ ] 7.8 Ensure all tests pass
- [ ] 7.9 Update spec documentation
- [ ] 7.10 Create release checklist

### Testing for Phase 7
```bash
# All tests pass
pytest tests/ -v --cov=topdf --cov-report=term-missing

# Code quality
black topdf/ tests/
ruff check topdf/ tests/
mypy topdf/

# Documentation review
cat README.md

# Final smoke test
pip uninstall topdf -y
pip install -e .
topdf --version
topdf --help
topdf https://docsend.com/view/TEST_LINK
```

### Exit Criteria
- [ ] README.md is complete and accurate
- [ ] All tests pass with >85% coverage
- [ ] Code passes linting
- [ ] Fresh install works
- [ ] Tool is ready for daily use

---

## Phase 8: AI Summarization (Optional)
**Goal**: Add optional AI-powered structured analysis with Perplexity (single provider)

### Tasks
- [ ] 8.1 Create `config.py` for Perplexity API key management
- [ ] 8.2 Add `SummaryError` and `OCRError` to `exceptions.py`
- [ ] 8.3 Create `summarizer.py` with OCR + Perplexity (single API call)
- [ ] 8.4 Modify `converter.py` to include screenshots in result
- [ ] 8.5 Add interactive summary prompt to `cli.py`
- [ ] 8.6 Add `--check-key` and `--reset-key` flags to `cli.py`
- [ ] 8.7 Update `pyproject.toml` with optional dependencies
- [ ] 8.8 Write tests for `config.py`
- [ ] 8.9 Write tests for `summarizer.py`
- [ ] 8.10 Manual E2E testing

### Testing for Phase 8
```bash
# Unit tests
pytest tests/test_config.py -v
pytest tests/test_summarizer.py -v

# API key management tests
topdf --check-key
topdf --reset-key

# Integration test with mocked API
pytest tests/test_integration.py::test_summary_after_conversion -v

# Manual E2E test (requires Perplexity API key)
topdf https://docsend.com/view/LINK
# Answer 'y' to summary prompt
# Enter Perplexity API key when prompted
# Verify .md file created with structured content + peers table

# Test graceful degradation
# Use invalid API key
# Verify PDF still saved, warning shown
```

### Exit Criteria
- [ ] Structured analysis + peer search works with single Perplexity call
- [ ] Perplexity API key persists correctly in `~/.config/topdf/config.json`
- [ ] `--check-key` shows masked key status
- [ ] `--reset-key` clears saved key with confirmation
- [ ] Summary failure does not break PDF conversion
- [ ] All tests pass

### Acceptance Criteria (Summarization Feature)

Complete checklist for feature sign-off:

1. [ ] User can generate summary after PDF conversion via interactive prompt
2. [ ] Summary includes ≤200 character company description
3. [ ] Summary includes primary and secondary sector tags
4. [ ] Summary includes early customer traction (yes/no + details)
5. [ ] Summary includes funded peers table (up to 10 companies)
6. [ ] Markdown file created with same name as PDF (e.g., `Company.pdf` → `Company.md`)
7. [ ] Single Perplexity API call handles both analysis and peer search
8. [ ] API key can be persisted to config file
9. [ ] API key can be loaded from environment variable
10. [ ] `--check-key` shows masked key status
11. [ ] `--reset-key` clears saved key with confirmation
12. [ ] Summary failure does not affect PDF conversion
13. [ ] All unit and integration tests pass

---

# 7. Testing Strategy

## 7.1 Test Pyramid

```
                    ┌─────────────┐
                    │   Manual    │  ← Real DocSend links
                    │   E2E       │  ← 5-10 tests
                    ├─────────────┤
                    │ Integration │  ← Component combinations
                    │   Tests     │  ← 15-20 tests
                    ├─────────────┤
                    │    Unit     │  ← Individual functions
                    │    Tests    │  ← 40-50 tests
                    └─────────────┘
```

## 7.2 Unit Tests

### scraper.py Tests
| Test Case | Description |
|-----------|-------------|
| `test_url_validation_valid` | Accept valid DocSend URLs |
| `test_url_validation_invalid` | Reject non-DocSend URLs |
| `test_page_count_parsing` | Extract page count from DOM |
| `test_screenshot_is_png` | Screenshots are valid PNG |
| `test_retry_on_failure` | Retry logic works |
| `test_timeout_handling` | Timeout raises exception |

### auth.py Tests
| Test Case | Description |
|-----------|-------------|
| `test_detect_email_gate` | Detect email-only gate |
| `test_detect_passcode_gate` | Detect passcode gate |
| `test_detect_no_auth` | Detect open document |
| `test_email_form_fill` | Email form filled correctly |
| `test_passcode_form_fill` | Both fields filled |
| `test_invalid_email_error` | Clear error message |

### pdf_builder.py Tests
| Test Case | Description |
|-----------|-------------|
| `test_single_page_pdf` | PDF with one page |
| `test_multi_page_pdf` | PDF with multiple pages |
| `test_page_order` | Pages in correct order |
| `test_image_resize` | Large images resized |
| `test_empty_input` | Error on empty list |
| `test_pdf_is_valid` | Output is valid PDF |

### name_extractor.py Tests
| Test Case | Description |
|-----------|-------------|
| `test_title_parse_standard` | "Company - Deck \| DocSend" |
| `test_title_parse_minimal` | "Company Name" |
| `test_sanitize_slashes` | Remove / and \ |
| `test_sanitize_colons` | Remove : |
| `test_sanitize_quotes` | Remove quotes |
| `test_truncate_long_name` | Limit to 100 chars |
| `test_duplicate_handling` | Append (1), (2), etc |

### cli.py Tests
| Test Case | Description |
|-----------|-------------|
| `test_help_flag` | --help shows usage |
| `test_version_flag` | --version shows version |
| `test_missing_url` | Error without URL |
| `test_invalid_url` | Error for non-DocSend |
| `test_all_options` | All flags parsed correctly |

### config.py Tests
| Test Case | Description |
|-----------|-------------|
| `test_get_api_key_from_config` | Key retrieved from config file |
| `test_get_api_key_from_env` | Key retrieved from ENV var |
| `test_config_precedence` | Config file takes precedence over ENV |
| `test_get_api_key_missing` | Returns None when no key exists |
| `test_save_api_key` | Key saved to config file |
| `test_save_creates_directory` | Creates ~/.config/topdf/ if missing |
| `test_clear_api_keys` | All keys removed from config |
| `test_has_api_key_true` | Returns True when key exists |
| `test_has_api_key_false` | Returns False when no key |
| `test_get_masked_key` | Returns sk-ant-****...****  format |

### summarizer.py Tests
| Test Case | Description |
|-----------|-------------|
| `test_extract_text_success` | OCR extracts text from screenshots |
| `test_extract_text_no_tesseract` | Raises OCRError if tesseract missing |
| `test_extract_text_empty` | Raises OCRError if no text found |
| `test_max_pages_limit` | Only first 5 pages processed |
| `test_build_prompt` | Prompt includes text and company name |
| `test_call_anthropic` | Mock API returns summary |
| `test_call_openai` | Mock API returns summary |
| `test_api_error` | Raises SummaryError on API failure |
| `test_write_summary` | Markdown file created with correct format |
| `test_write_summary_path` | .md file created alongside PDF |
| `test_summarize_e2e` | Full flow with mocked LLM |

## 7.3 Integration Tests

| Test Case | Components | Description |
|-----------|------------|-------------|
| `test_scraper_to_pdf` | scraper + pdf_builder | Screenshots convert to PDF |
| `test_full_open_flow` | all | Open DocSend end-to-end |
| `test_full_email_flow` | all + auth | Email-protected end-to-end |
| `test_name_extraction_integration` | scraper + name_extractor | Name from real page |
| `test_output_directory_creation` | cli + filesystem | Creates dir if missing |
| `test_summary_after_conversion` | converter + summarizer | Summary generated after PDF |
| `test_summary_with_anthropic` | summarizer + API | Anthropic provider works |
| `test_summary_with_openai` | summarizer + API | OpenAI provider works |
| `test_summary_failure_graceful` | cli + summarizer | PDF saved even if summary fails |
| `test_api_key_persistence` | cli + config | Keys saved and loaded |
| `test_check_key_flag` | cli + config | Shows masked keys |
| `test_reset_key_flag` | cli + config | Clears saved keys |

## 7.4 Manual E2E Test Cases

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| E2E-1 | Open document | `topdf <open_url>` | PDF saved with company name |
| E2E-2 | Email protected | `topdf <url> -e email` | PDF saved after auth |
| E2E-3 | Passcode protected | `topdf <url> -e email -p pass` | PDF saved after auth |
| E2E-4 | Invalid URL | `topdf https://google.com` | Clear error message |
| E2E-5 | Network timeout | Disconnect wifi mid-scrape | Graceful error |
| E2E-6 | Name override | `topdf <url> --name "Test"` | Saved as "Test.pdf" |
| E2E-7 | Custom output | `topdf <url> -o ~/Desktop` | Saved to Desktop |
| E2E-8 | Duplicate name | Run twice with same URL | Second file has (1) |
| E2E-9 | Large deck (50+ pages) | `topdf <large_deck_url>` | All pages captured |
| E2E-10 | Interactive prompt | `topdf <protected_url>` (no flags) | Prompts for credentials |
| E2E-11 | Generate summary | Convert, say yes to summary prompt | .md file created alongside PDF |
| E2E-12 | Skip summary | Convert, say no to summary prompt | Only PDF created |
| E2E-13 | Anthropic provider | Select Anthropic, provide key | Summary generated |
| E2E-14 | OpenAI provider | Select OpenAI, provide key | Summary generated |
| E2E-15 | Persist API key | Enter key, save it | Key works on next run |
| E2E-16 | Check API key | `topdf --check-key` | Shows masked key |
| E2E-17 | Reset API key | `topdf --reset-key` | Keys cleared with confirmation |
| E2E-18 | Summary failure | Use invalid API key | Warning shown, PDF still saved |

## 7.5 Test Data Requirements

For integration/E2E testing, you'll need access to:
1. **Open DocSend link** - No authentication required
2. **Email-gated DocSend link** - Requires email entry
3. **Passcode-protected DocSend link** - Requires email + passcode

**Recommendation**: Create test documents on your own DocSend account for reliable testing.

## 7.6 CI/CD Test Commands

```bash
# Quick test (unit only)
pytest tests/ -v --ignore=tests/test_integration.py

# Full test suite
pytest tests/ -v --cov=topdf --cov-report=html

# With real DocSend URLs (set env vars)
DOCSEND_OPEN_URL=... DOCSEND_EMAIL_URL=... pytest tests/test_integration.py -v
```

---

# Summary

This specification provides a complete blueprint for building a privacy-preserving DocSend-to-PDF converter. The recommended approach (Playwright browser automation) ensures confidential pitch decks never leave your machine while providing full control over authentication scenarios.

**Key deliverables**:
- Python CLI tool installable via `pip install -e .`
- Command: `topdf <docsend_url>` with auth and naming options
- Output: Company-named PDFs in `converted PDFs/` folder
- Optional AI summarization with markdown output
- 8 implementation phases with testing at each step

**Next step**: Begin Phase 1 implementation (or Phase 8 for summarization feature).
