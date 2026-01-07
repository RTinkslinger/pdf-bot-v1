# Requirements Specification

## Document Info
- **Project**: DocSend to PDF Converter (topdf)
- **Version**: 1.0
- **Last Updated**: 2025-01-07

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

---

## 2. Non-Functional Requirements

### NFR-1: Privacy & Security

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-1.1 | All processing must happen locally | Must Have | No external API calls |
| NFR-1.2 | No document data transmitted externally | Must Have | Network traffic verified |
| NFR-1.3 | No logging of document content or URLs | Must Have | No sensitive logs |
| NFR-1.4 | Credentials not stored persistently | Should Have | No credential files |

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

---

## 6. Glossary

| Term | Definition |
|------|------------|
| DocSend | Document sharing platform with analytics |
| Email gate | Authentication requiring email entry |
| Passcode | Additional password for protected docs |
| OCR | Optical Character Recognition |
| Headless browser | Browser without GUI for automation |
