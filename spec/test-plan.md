# Test Plan

## Document Info
- **Project**: DocSend to PDF Converter (topdf)
- **Version**: 1.0
- **Last Updated**: 2025-01-07

---

## 1. Testing Strategy

### 1.1 Test Pyramid

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

### 1.2 Coverage Targets

| Level | Target Coverage | Tool |
|-------|-----------------|------|
| Unit Tests | >90% | pytest-cov |
| Integration Tests | >80% | pytest-cov |
| Overall | >85% | pytest-cov |

---

## 2. Unit Tests

### 2.1 scraper.py Tests

| Test ID | Test Case | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| SCR-001 | `test_url_validation_valid` | Valid DocSend URL | Returns True |
| SCR-002 | `test_url_validation_invalid` | Non-DocSend URL | Raises InvalidURLError |
| SCR-003 | `test_url_validation_malformed` | Malformed URL | Raises InvalidURLError |
| SCR-004 | `test_page_count_parsing` | Extract "1 of 24" | Returns 24 |
| SCR-005 | `test_page_count_single` | Single page doc | Returns 1 |
| SCR-006 | `test_screenshot_is_png` | Capture returns PNG | Valid PNG bytes |
| SCR-007 | `test_retry_on_failure` | First attempt fails | Succeeds on retry |
| SCR-008 | `test_max_retries_exceeded` | All retries fail | Raises ScrapingError |
| SCR-009 | `test_timeout_handling` | Page load timeout | Raises TimeoutError |
| SCR-010 | `test_browser_cleanup` | Normal exit | Browser process terminated |

### 2.2 auth.py Tests

| Test ID | Test Case | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| AUTH-001 | `test_detect_email_gate` | Email form present | Returns AuthType.EMAIL |
| AUTH-002 | `test_detect_passcode_gate` | Passcode form present | Returns AuthType.PASSCODE |
| AUTH-003 | `test_detect_no_auth` | No auth required | Returns AuthType.NONE |
| AUTH-004 | `test_email_form_fill` | Fill email field | Form submitted |
| AUTH-005 | `test_passcode_form_fill` | Fill email + passcode | Form submitted |
| AUTH-006 | `test_invalid_email_error` | Wrong email | Returns False |
| AUTH-007 | `test_invalid_passcode_error` | Wrong passcode | Returns False |
| AUTH-008 | `test_email_prompt_shown` | No email provided | Prompts user |

### 2.3 pdf_builder.py Tests

| Test ID | Test Case | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| PDF-001 | `test_single_page_pdf` | One screenshot | Valid 1-page PDF |
| PDF-002 | `test_multi_page_pdf` | 10 screenshots | Valid 10-page PDF |
| PDF-003 | `test_page_order` | Pages 1,2,3 | Correct order in PDF |
| PDF-004 | `test_image_resize` | Large image input | Resized to standard |
| PDF-005 | `test_empty_input` | Empty screenshot list | Raises PDFBuildError |
| PDF-006 | `test_pdf_is_valid` | Generated PDF | Opens without error |
| PDF-007 | `test_pdf_size_reasonable` | 20-page PDF | <5MB |
| PDF-008 | `test_corrupt_image` | Invalid PNG bytes | Raises PDFBuildError |

### 2.4 name_extractor.py Tests

| Test ID | Test Case | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| NAME-001 | `test_title_parse_standard` | "Acme - Deck \| DocSend" | "Acme" |
| NAME-002 | `test_title_parse_with_dash` | "Series A - Inc \| DocSend" | "Series A - Inc" |
| NAME-003 | `test_title_parse_minimal` | "Company XYZ" | "Company XYZ" |
| NAME-004 | `test_title_parse_empty` | "" | Returns None |
| NAME-005 | `test_sanitize_slashes` | "Company/Inc" | "Company-Inc" |
| NAME-006 | `test_sanitize_colons` | "Startup: AI" | "Startup - AI" |
| NAME-007 | `test_sanitize_quotes` | 'Name "Test"' | "Name Test" |
| NAME-008 | `test_truncate_long_name` | 200 char name | Truncated to 100 |
| NAME-009 | `test_ocr_extraction` | Image with text | Extracts company |
| NAME-010 | `test_duplicate_handling` | File exists | Returns "Name (1)" |

### 2.5 cli.py Tests

| Test ID | Test Case | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| CLI-001 | `test_help_flag` | `topdf --help` | Shows usage |
| CLI-002 | `test_version_flag` | `topdf --version` | Shows version |
| CLI-003 | `test_missing_url` | `topdf` (no args) | Error message |
| CLI-004 | `test_invalid_url` | Non-DocSend URL | Error message |
| CLI-005 | `test_email_option` | `-e user@test.com` | Email passed |
| CLI-006 | `test_passcode_option` | `-p secret123` | Passcode passed |
| CLI-007 | `test_name_option` | `--name "Custom"` | Name override |
| CLI-008 | `test_output_option` | `-o ~/Desktop` | Custom output dir |
| CLI-009 | `test_verbose_flag` | `-v` | Verbose enabled |

---

## 3. Integration Tests

### 3.1 Component Integration

| Test ID | Test Case | Components | Description |
|---------|-----------|------------|-------------|
| INT-001 | `test_scraper_to_pdf` | scraper + pdf_builder | Screenshots → PDF |
| INT-002 | `test_scraper_with_auth` | scraper + auth | Auth flow works |
| INT-003 | `test_name_extraction_pipeline` | scraper + name_extractor | Title → filename |
| INT-004 | `test_full_open_flow` | all | Open DocSend end-to-end |
| INT-005 | `test_full_email_flow` | all + auth | Email-protected e2e |
| INT-006 | `test_full_passcode_flow` | all + auth | Passcode-protected e2e |
| INT-007 | `test_output_directory_creation` | cli + filesystem | Creates dir if missing |
| INT-008 | `test_duplicate_file_handling` | converter + filesystem | Handles existing files |

### 3.2 Error Handling Integration

| Test ID | Test Case | Scenario | Expected |
|---------|-----------|----------|----------|
| ERR-001 | `test_network_error` | Connection lost | Graceful error |
| ERR-002 | `test_invalid_credentials` | Wrong email | Clear error msg |
| ERR-003 | `test_page_load_timeout` | Slow network | Timeout error |
| ERR-004 | `test_document_not_found` | 404 page | Clear error msg |

---

## 4. Manual E2E Test Cases

### 4.1 Test Scenarios

| ID | Scenario | Preconditions | Steps | Expected Result |
|----|----------|---------------|-------|-----------------|
| E2E-01 | Open document | Open DocSend URL | `topdf <url>` | PDF saved with company name |
| E2E-02 | Email protected | Email-gated URL | `topdf <url> -e email` | PDF saved after auth |
| E2E-03 | Passcode protected | Passcode URL | `topdf <url> -e email -p pass` | PDF saved after auth |
| E2E-04 | Invalid URL | None | `topdf https://google.com` | Clear error message |
| E2E-05 | Network timeout | Disconnect wifi | Start conversion | Graceful error |
| E2E-06 | Name override | Any URL | `topdf <url> --name "Test"` | Saved as "Test.pdf" |
| E2E-07 | Custom output | Any URL | `topdf <url> -o ~/Desktop` | Saved to Desktop |
| E2E-08 | Duplicate name | File exists | Run twice same URL | Second file has (1) |
| E2E-09 | Large deck | 50+ page doc | `topdf <large_url>` | All pages captured |
| E2E-10 | Interactive prompt | Protected URL | `topdf <url>` (no flags) | Prompts for credentials |

### 4.2 Test Data Requirements

| Type | Source | Purpose |
|------|--------|---------|
| Open DocSend | Create test account | Test basic flow |
| Email-gated | Configure on DocSend | Test email auth |
| Passcode-protected | Configure on DocSend | Test passcode auth |
| Large document | Upload 50-page PDF | Test performance |

---

## 5. Test Execution

### 5.1 Commands

```bash
# Run all unit tests
pytest tests/ -v --ignore=tests/test_integration.py

# Run with coverage
pytest tests/ -v --cov=topdf --cov-report=html

# Run specific module tests
pytest tests/test_scraper.py -v

# Run integration tests (requires env vars)
DOCSEND_OPEN_URL=<url> pytest tests/test_integration.py -v

# Run with verbose output
pytest tests/ -v -s

# Run until first failure
pytest tests/ -x
```

### 5.2 Environment Variables for Integration Tests

```bash
export DOCSEND_OPEN_URL="https://docsend.com/view/OPEN_TEST"
export DOCSEND_EMAIL_URL="https://docsend.com/view/EMAIL_TEST"
export DOCSEND_PASSCODE_URL="https://docsend.com/view/PASS_TEST"
export DOCSEND_TEST_EMAIL="test@example.com"
export DOCSEND_TEST_PASSCODE="testpass123"
```

---

## 6. Test Fixtures

### 6.1 conftest.py Structure

```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_screenshot():
    """Load a sample PNG screenshot for testing."""
    return Path("tests/fixtures/sample_page.png").read_bytes()

@pytest.fixture
def mock_page_title():
    """Sample DocSend page title."""
    return "Acme Corp - Series A Pitch Deck | DocSend"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output = tmp_path / "converted PDFs"
    output.mkdir()
    return output

@pytest.fixture
async def mock_browser():
    """Mock Playwright browser for unit tests."""
    # Return mock browser instance
    pass
```

### 6.2 Mock Objects

| Mock | Purpose |
|------|---------|
| `MockPage` | Simulate Playwright page |
| `MockBrowser` | Simulate browser launch |
| `MockResponse` | Simulate HTTP responses |

---

## 7. Continuous Integration

### 7.1 GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        playwright install chromium

    - name: Install Tesseract
      run: brew install tesseract

    - name: Run tests
      run: pytest tests/ -v --cov=topdf --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 8. Test Reporting

### 8.1 Coverage Report

Generate HTML coverage report:
```bash
pytest tests/ --cov=topdf --cov-report=html
open htmlcov/index.html
```

### 8.2 Test Results Format

```
==================== test session starts ====================
platform darwin -- Python 3.11.0
collected 50 items

tests/test_cli.py ......... [18%]
tests/test_scraper.py ............. [44%]
tests/test_auth.py ........ [60%]
tests/test_pdf_builder.py ........ [76%]
tests/test_name_extractor.py ........... [98%]
tests/test_integration.py . [100%]

==================== 50 passed in 12.34s ====================
```

---

## 9. Bug Tracking

### 9.1 Test Failure Protocol

1. Document failure in issue tracker
2. Include:
   - Test name
   - Error message
   - Stack trace
   - Steps to reproduce
3. Assign priority based on impact
4. Create fix branch
5. Add regression test if needed

### 9.2 Severity Levels

| Level | Definition | Response |
|-------|------------|----------|
| Critical | Blocks all usage | Fix immediately |
| High | Major feature broken | Fix within 24h |
| Medium | Minor feature affected | Fix within 1 week |
| Low | Edge case / cosmetic | Fix when convenient |

---

## 10. Test Schedule

### 10.1 Per-Phase Testing

| Phase | Tests to Run | Timing |
|-------|--------------|--------|
| Phase 1 | CLI unit tests | After CLI setup |
| Phase 2 | Scraper unit tests | After scraper impl |
| Phase 3 | Auth unit tests | After auth impl |
| Phase 4 | PDF builder tests | After builder impl |
| Phase 5 | Name extractor tests | After extractor impl |
| Phase 6 | All integration tests | After integration |
| Phase 7 | Full E2E suite | Before release |

### 10.2 Regression Testing

Run full test suite:
- Before each PR merge
- After any dependency update
- Before any release
