# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**topdf** - A Python CLI tool that converts DocSend links to PDF files. Designed for investors to locally convert pitch decks while preserving privacy. Optional AI summarization generates structured company analysis (description, sectors, traction) and finds recently funded peer companies using Perplexity.

## Commands

```bash
# Install for development
pip install -e .
playwright install chromium
brew install tesseract  # macOS system dependency

# Run CLI
topdf <docsend_url>
topdf <url> --email user@example.com --passcode secret
topdf <url> --name "Custom Name" --output ~/Desktop
topdf --check-key   # Show configured API keys
topdf --reset-key   # Clear saved API keys

# Run tests
pytest tests/ -v
pytest tests/test_scraper.py -v  # single module
pytest tests/ --cov=topdf --cov-report=html  # with coverage

# Code quality
black topdf/ tests/
ruff check topdf/ tests/
mypy topdf/
```

## Architecture

```
CLI (cli.py) → Converter (converter.py) → Scraper (scraper.py) → Auth (auth.py)
                                        → PDFBuilder (pdf_builder.py)
                                        → NameExtractor (name_extractor.py)
            → [Optional] Summarizer (summarizer.py) → Config (config.py)
```

**Conversion flow:**
1. Scraper uses Playwright to open DocSend in headless Chromium
2. Auth handler detects and fills email/passcode gates if required
3. Scraper captures screenshots of each page
4. NameExtractor parses page title (fallback: OCR first slide)
5. PDFBuilder combines screenshots into PDF using img2pdf
6. Output saved to `converted PDFs/{company_name}.pdf`
7. [Optional] User prompted for AI summary:
   - OCR first 5 pages → Perplexity analyzes deck + finds funded peers (single API call)
   - Markdown file with company overview + peers table

## Key Design Decisions

- **Playwright over API**: DocSend renders client-side; no public download API
- **Screenshot capture**: Preserves exact visual fidelity of slides
- **Local-only processing**: Privacy requirement - no document data leaves machine
- **Name extraction fallback chain**: Page title → OCR → User prompt

## Tech Stack

- **playwright**: Browser automation
- **click**: CLI framework
- **img2pdf**: PDF generation
- **pytesseract**: OCR for name extraction and summarization
- **rich**: Progress bars and output
- **Pillow**: Image processing
- **openai**: Perplexity API (uses OpenAI-compatible SDK, optional)

## Exception Hierarchy

All custom exceptions inherit from `TopdfError` in `exceptions.py`:
- `InvalidURLError`, `AuthenticationError`, `ScrapingError`, `PDFBuildError`, `TimeoutError`
- `SummaryError`, `OCRError` (for summarization)

## Specifications

Detailed specs are in `spec/`:
- `SPEC.md` - Full specification with 8-phase implementation plan
- `architecture.md` - Component specifications and data flow
- `requirements.md` - Functional and non-functional requirements
- `test-plan.md` - Test cases and coverage targets

**API Keys:** Stored in `~/.config/topdf/config.json` (Perplexity only)

## Changelog Management

This project uses branch-specific changelog files to document iterations.

### Before Starting Work
1. Check if `changelog/{branch-name}.md` exists for the current branch
2. If NOT, prompt the user to run: `./scripts/setup-hooks.sh`
3. The hook will auto-create changelog files for new branches going forward

### After Each Iteration
When you complete a meaningful unit of work (bug fix, feature, refactor), update the changelog:

1. Get current branch: `git branch --show-current`
2. Convert to filename: replace `/` with `-` (e.g., `fix/bug` → `fix-bug.md`)
3. Update `changelog/{branch-name}.md` with:
   - Iteration number (increment from last)
   - Objective
   - Files modified
   - Changes made
   - Test results

### Changelog Template
```
## Iteration N: [Title]

**Objective:** [What you're trying to achieve]

**Files Modified:**
- `path/to/file`

### Changes Made:
1. [Change description]

### Test Results:
- [Test outcome]

---
```
