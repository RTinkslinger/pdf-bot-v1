# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**topdf** - A Python CLI tool that converts DocSend links to PDF files. Designed for investors to locally convert pitch decks while preserving privacy (no third-party APIs).

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
```

**Conversion flow:**
1. Scraper uses Playwright to open DocSend in headless Chromium
2. Auth handler detects and fills email/passcode gates if required
3. Scraper captures screenshots of each page
4. NameExtractor parses page title (fallback: OCR first slide)
5. PDFBuilder combines screenshots into PDF using img2pdf
6. Output saved to `converted PDFs/{company_name}.pdf`

## Key Design Decisions

- **Playwright over API**: DocSend renders client-side; no public download API
- **Screenshot capture**: Preserves exact visual fidelity of slides
- **Local-only processing**: Privacy requirement - no document data leaves machine
- **Name extraction fallback chain**: Page title → OCR → User prompt

## Tech Stack

- **playwright**: Browser automation
- **click**: CLI framework
- **img2pdf**: PDF generation
- **pytesseract**: OCR for name extraction
- **rich**: Progress bars and output
- **Pillow**: Image processing

## Exception Hierarchy

All custom exceptions inherit from `TopdfError` in `exceptions.py`:
- `InvalidURLError`, `AuthenticationError`, `ScrapingError`, `PDFBuildError`, `TimeoutError`

## Specifications

Detailed specs are in `spec/`:
- `SPEC.md` - Full specification with 7-phase implementation plan
- `architecture.md` - Component specifications and data flow
- `requirements.md` - Functional and non-functional requirements
- `test-plan.md` - Test cases and coverage targets
