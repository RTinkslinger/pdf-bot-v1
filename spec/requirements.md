# Requirements Specification

## Document Info
- **Project**: DocSend to PDF Converter (topdf)
- **Version**: 1.1
- **Last Updated**: 2025-01-07
- **Changes**: Added FR-5 (Summarization), FR-6 (API Key Management), updated NFR-1 (Privacy)

---

## 1. Functional Requirements

### FR-1: Core Conversion

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1.1 | Accept DocSend URL as input via CLI command `topdf <url>` | Must Have | URL is validated and processed |
| FR-1.2 | Convert DocSend document to PDF format | Must Have | Output is valid PDF file |
| FR-1.3 | Support multi-page documents (10-50+ pages) | Must Have | All pages captured in order |
| FR-1.4 | Preserve visual fidelity of original document | Must Have | Screenshots match original |
| FR-1.5 | Generate searchable PDF with text layer (OCR) | Nice to Have | Text is selectable in PDF |

### FR-2: Authentication Handling

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-2.1 | Support open/public DocSend links | Must Have | No auth required for open links |
| FR-2.2 | Support email-gated DocSend links | Must Have | Can enter email to access |
| FR-2.3 | Support passcode-protected DocSend links | Must Have | Can enter email + passcode |
| FR-2.4 | Prompt user for credentials when required | Must Have | Interactive prompt appears |
| FR-2.5 | Accept credentials via CLI flags | Should Have | `--email` and `--passcode` work |

### FR-3: File Naming & Organization

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-3.1 | Automatically extract company name from document | Must Have | Name extracted from title/OCR |
| FR-3.2 | Save PDF with company name as filename | Must Have | File named appropriately |
| FR-3.3 | Store converted PDFs in `converted PDFs/` folder | Must Have | Correct output directory |
| FR-3.4 | Allow manual override of filename via `--name` | Should Have | Custom names work |
| FR-3.5 | Handle filename conflicts | Should Have | Appends (1), (2), etc. |

### FR-4: User Experience

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-4.1 | Show progress indicator during conversion | Should Have | Visual progress shown |
| FR-4.2 | Display success message with output file path | Must Have | Clear success output |
| FR-4.3 | Provide clear error messages for failures | Must Have | Errors are actionable |
| FR-4.4 | Support `--help` flag with usage documentation | Must Have | Help text displays |
| FR-4.5 | Support `--version` flag | Should Have | Version number shown |

### FR-5: AI Summarization (Optional)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-5.1 | Prompt for AI summary after PDF conversion | Should Have | Interactive prompt appears |
| FR-5.2 | Extract text from screenshots using OCR | Should Have | Text extracted from first 5 pages |
| FR-5.3 | Generate structured company analysis via Perplexity | Should Have | JSON with name, description, sector, customers |
| FR-5.4 | Generate ≤200 character company description | Should Have | Description meets length requirement |
| FR-5.5 | Assign sector tags (primary + secondary) | Should Have | Tags from predefined list |
| FR-5.6 | Identify early customer traction | Should Have | Yes/No with details if available |
| FR-5.7 | Find recently funded peers via Perplexity | Should Have | Up to 10 peers from last 24 months |
| FR-5.8 | Save summary as markdown file alongside PDF | Should Have | .md file created with same name |
| FR-5.9 | Summary failure must not break PDF conversion | Must Have | PDF saved even if summary fails |

### FR-6: API Key Management

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-6.1 | Store Perplexity API key in `~/.config/topdf/config.json` | Should Have | Key persists across sessions |
| FR-6.2 | Support API key via environment variable (PERPLEXITY_API_KEY) | Should Have | ENV var detected and used |
| FR-6.3 | Config file takes precedence over ENV var | Should Have | Correct priority order |
| FR-6.4 | Prompt for API key if not configured | Should Have | Masked input prompt shown |
| FR-6.5 | Offer to save key after manual entry | Should Have | User can choose to persist |
| FR-6.6 | Support `--check-key` flag to show configured key | Should Have | Masked key display |
| FR-6.7 | Support `--reset-key` flag to clear saved key | Should Have | Confirmation then deletion |

---

## 2. Non-Functional Requirements

### NFR-1: Privacy & Security

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-1.1 | Core PDF conversion must happen locally | Must Have | No external API calls for PDF |
| NFR-1.2 | Document data only sent to LLM if user opts in | Must Have | Explicit consent required |
| NFR-1.3 | No logging of document content or URLs | Must Have | No sensitive logs |
| NFR-1.4 | DocSend credentials not stored persistently | Should Have | No credential files |
| NFR-1.5 | API keys stored locally only | Should Have | Keys in ~/.config/topdf/ |
| NFR-1.6 | Clear privacy messaging for API key storage | Should Have | User informed of local storage |
| NFR-1.7 | API keys never logged or displayed in full | Should Have | Masked display only |

### NFR-2: Performance

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-2.1 | Convert 20-page deck in under 60 seconds | Should Have | Timing meets target |
| NFR-2.2 | Memory footprint under 500MB | Should Have | Memory usage monitored |
| NFR-2.3 | Browser instance properly cleaned up | Should Have | No zombie processes |

### NFR-3: Reliability

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-3.1 | Handle network timeouts gracefully | Should Have | Timeout produces error |
| NFR-3.2 | Retry failed page captures (max 3) | Should Have | Transient failures handled |
| NFR-3.3 | Produce valid PDF even if OCR fails | Must Have | OCR is optional |
| NFR-3.4 | Handle DocSend unavailability | Should Have | Clear error message |

### NFR-4: Maintainability

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-4.1 | Modular code architecture | Should Have | Separate modules |
| NFR-4.2 | Handle DocSend UI changes easily | Should Have | Selectors configurable |
| NFR-4.3 | Comprehensive test coverage (>85%) | Should Have | Test coverage report |
| NFR-4.4 | Type hints throughout codebase | Nice to Have | mypy passes |

---

## 3. Constraints

### Technical Constraints
- **Platform**: macOS (primary), Linux (secondary)
- **Python Version**: 3.9 or higher
- **System Dependencies**: Tesseract OCR
- **Browser**: Chromium (via Playwright)

### Operational Constraints
- **Network**: Requires internet access
- **Storage**: ~50-100MB per converted PDF
- **Concurrent Use**: Single instance recommended

---

## 4. Assumptions

1. DocSend's web interface remains relatively stable
2. User has valid email/passcode when required
3. Documents are standard pitch deck format
4. User has permissions to download shared documents

---

## 5. Dependencies

### External Dependencies
| Dependency | Version | Purpose |
|------------|---------|---------|
| playwright | >=1.40.0 | Browser automation |
| Pillow | >=10.0.0 | Image processing |
| img2pdf | >=0.5.0 | PDF creation |
| pytesseract | >=0.3.10 | OCR |
| click | >=8.1.0 | CLI framework |
| rich | >=13.0.0 | Progress bars |

### System Dependencies
| Dependency | Installation | Purpose |
|------------|--------------|---------|
| Tesseract | `brew install tesseract` | OCR engine |
| Chromium | `playwright install chromium` | Headless browser |

### Optional Dependencies (Summarization)
| Dependency | Version | Purpose |
|------------|---------|---------|
| openai | >=1.0.0 | Perplexity API (uses OpenAI-compatible SDK) |

**Installation:** `pip install topdf[summarize]`

**Note:** Perplexity API uses the OpenAI SDK with `base_url="https://api.perplexity.ai"`

---

## 6. Glossary

| Term | Definition |
|------|------------|
| DocSend | Document sharing platform with analytics |
| Email gate | Authentication requiring email entry |
| Passcode | Additional password for protected docs |
| OCR | Optical Character Recognition |
| Headless browser | Browser without GUI for automation |
| LLM | Large Language Model (e.g., Claude, GPT) |
| API Key | Authentication credential for LLM services |
| Summarization | AI-generated structured analysis from pitch deck |
| Perplexity | AI search API for finding funded peer companies |
| Sector Tag | Category classification (e.g., fintech, cybersecurity) |
| Funded Peers | Similar companies that raised venture funding recently |
