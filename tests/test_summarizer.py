"""Tests for summarizer module."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image, ImageDraw

from topdf import summarizer
from topdf.exceptions import OCRError, SummaryError


@pytest.fixture
def sample_screenshot_with_text() -> bytes:
    """Create a screenshot with readable text for OCR testing."""
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Add some text content
    draw.text((50, 50), "Acme Corporation", fill=(0, 0, 0))
    draw.text((50, 100), "B2B SaaS Platform", fill=(0, 0, 0))
    draw.text((50, 150), "Enterprise Sales Analytics", fill=(0, 0, 0))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def sample_screenshots_for_ocr(sample_screenshot_with_text) -> list[bytes]:
    """Multiple screenshots for OCR testing."""
    return [sample_screenshot_with_text] * 3


@pytest.fixture
def mock_perplexity_response():
    """Mock Perplexity API response."""
    return {
        "company": {
            "company_name": "Acme Corp",
            "description": "B2B SaaS platform for enterprise sales analytics",
            "has_customers": True,
            "customer_details": "Fortune 500 logos shown",
            "primary_sector": "enterprise_tech",
            "secondary_sector": "fintech",
        },
        "funded_peers": [
            {
                "company_name": "Gong",
                "round_type": "Series E",
                "amount": "$250M",
                "date": "Jun 2024",
                "description": "Revenue intelligence platform",
            },
            {
                "company_name": "Clari",
                "round_type": "Series F",
                "amount": "$225M",
                "date": "Jan 2024",
                "description": "Revenue operations platform",
            },
        ],
    }


class TestCheckTesseract:
    """Tests for check_tesseract function."""

    def test_returns_bool(self):
        """Should return a boolean."""
        result = summarizer.check_tesseract()
        assert isinstance(result, bool)


class TestExtractText:
    """Tests for extract_text function."""

    def test_raises_ocr_error_when_no_tesseract(self, sample_screenshots_for_ocr, monkeypatch):
        """Should raise OCRError when tesseract not installed."""
        monkeypatch.setattr(summarizer, "check_tesseract", lambda: False)

        with pytest.raises(OCRError) as exc_info:
            summarizer.extract_text(sample_screenshots_for_ocr)

        assert "Tesseract not installed" in str(exc_info.value)

    def test_respects_max_pages_limit(self, sample_screenshots_for_ocr, monkeypatch):
        """Should only process up to max_pages screenshots."""
        monkeypatch.setattr(summarizer, "check_tesseract", lambda: True)

        # Create mock for pytesseract
        call_count = 0

        def mock_image_to_string(img):
            nonlocal call_count
            call_count += 1
            return f"Page {call_count} text"

        with patch("pytesseract.image_to_string", mock_image_to_string):
            # Pass 10 screenshots but limit to 2
            screenshots = sample_screenshots_for_ocr * 4  # 12 screenshots
            summarizer.extract_text(screenshots, max_pages=2)

        assert call_count == 2


class TestBuildPrompt:
    """Tests for _build_prompt function."""

    def test_includes_ocr_text(self):
        """Should include OCR text in prompt."""
        ocr_text = "Company XYZ - AI Platform"
        prompt = summarizer._build_prompt(ocr_text)

        assert "Company XYZ - AI Platform" in prompt

    def test_includes_sector_list(self):
        """Should include all allowed sectors."""
        prompt = summarizer._build_prompt("test text")

        for sector in summarizer.SECTORS:
            assert sector in prompt

    def test_requests_json_format(self):
        """Should request JSON response format."""
        prompt = summarizer._build_prompt("test text")

        assert "JSON" in prompt
        assert "company_name" in prompt
        assert "funded_peers" in prompt


class TestParseResponse:
    """Tests for _parse_response function."""

    def test_parses_valid_response(self, mock_perplexity_response):
        """Should parse valid JSON response."""
        response_text = json.dumps(mock_perplexity_response)
        result = summarizer._parse_response(response_text)

        assert isinstance(result, summarizer.StructuredSummary)
        assert result.company.company_name == "Acme Corp"
        assert len(result.funded_peers) == 2

    def test_handles_markdown_wrapped_json(self, mock_perplexity_response):
        """Should extract JSON from markdown code blocks."""
        response_text = f"```json\n{json.dumps(mock_perplexity_response)}\n```"
        result = summarizer._parse_response(response_text)

        assert result.company.company_name == "Acme Corp"

    def test_raises_error_for_invalid_json(self):
        """Should raise SummaryError for invalid JSON."""
        with pytest.raises(SummaryError) as exc_info:
            summarizer._parse_response("not valid json")

        assert "No JSON found" in str(exc_info.value)

    def test_raises_error_for_missing_company_name(self):
        """Should raise SummaryError when company_name missing."""
        response = {"company": {"description": "Test"}, "funded_peers": []}

        with pytest.raises(SummaryError) as exc_info:
            summarizer._parse_response(json.dumps(response))

        assert "Missing company_name" in str(exc_info.value)

    def test_truncates_long_description(self):
        """Should truncate description to 200 characters."""
        response = {
            "company": {
                "company_name": "Test Co",
                "description": "A" * 300,  # 300 characters
                "has_customers": False,
                "primary_sector": "fintech",
            },
            "funded_peers": [],
        }

        result = summarizer._parse_response(json.dumps(response))
        assert len(result.company.description) == 200

    def test_normalizes_sector_names(self):
        """Should normalize sector names to snake_case."""
        response = {
            "company": {
                "company_name": "Test Co",
                "description": "Test",
                "has_customers": False,
                "primary_sector": "Enterprise Tech",  # Space instead of underscore
            },
            "funded_peers": [],
        }

        result = summarizer._parse_response(json.dumps(response))
        assert result.company.primary_sector == "enterprise_tech"

    def test_handles_invalid_sector(self):
        """Should default to enterprise_tech for invalid sector."""
        response = {
            "company": {
                "company_name": "Test Co",
                "description": "Test",
                "has_customers": False,
                "primary_sector": "invalid_sector",
            },
            "funded_peers": [],
        }

        result = summarizer._parse_response(json.dumps(response))
        assert result.company.primary_sector == "enterprise_tech"

    def test_limits_peers_to_10(self, mock_perplexity_response):
        """Should limit funded peers to 10."""
        mock_perplexity_response["funded_peers"] = [
            {"company_name": f"Company {i}", "round_type": "Seed", "amount": "$1M", "date": "2024"}
            for i in range(15)
        ]

        result = summarizer._parse_response(json.dumps(mock_perplexity_response))
        assert len(result.funded_peers) == 10


class TestFormatMarkdown:
    """Tests for format_markdown function."""

    def test_includes_company_name_header(self, mock_perplexity_response):
        """Should include company name as header."""
        summary = summarizer._parse_response(json.dumps(mock_perplexity_response))
        markdown = summarizer.format_markdown(summary)

        assert "# Acme Corp" in markdown

    def test_includes_overview_section(self, mock_perplexity_response):
        """Should include overview section."""
        summary = summarizer._parse_response(json.dumps(mock_perplexity_response))
        markdown = summarizer.format_markdown(summary)

        assert "## Overview" in markdown
        assert summary.company.description in markdown

    def test_includes_traction_section(self, mock_perplexity_response):
        """Should include traction section."""
        summary = summarizer._parse_response(json.dumps(mock_perplexity_response))
        markdown = summarizer.format_markdown(summary)

        assert "## Traction" in markdown
        assert "**Early Customers:** Yes" in markdown

    def test_includes_sector_section(self, mock_perplexity_response):
        """Should include sector section."""
        summary = summarizer._parse_response(json.dumps(mock_perplexity_response))
        markdown = summarizer.format_markdown(summary)

        assert "## Sector" in markdown
        assert "**Primary:** enterprise_tech" in markdown
        assert "**Secondary:** fintech" in markdown

    def test_includes_peers_table(self, mock_perplexity_response):
        """Should include funded peers table."""
        summary = summarizer._parse_response(json.dumps(mock_perplexity_response))
        markdown = summarizer.format_markdown(summary)

        assert "## Funded Peers" in markdown
        assert "| Company | Round | Amount | Date | Description |" in markdown
        assert "Gong" in markdown
        assert "Series E" in markdown

    def test_handles_no_peers(self, mock_perplexity_response):
        """Should handle case with no peers."""
        mock_perplexity_response["funded_peers"] = []
        summary = summarizer._parse_response(json.dumps(mock_perplexity_response))
        markdown = summarizer.format_markdown(summary)

        assert "No recent funding data found" in markdown


class TestWriteSummary:
    """Tests for write_summary function."""

    def test_creates_markdown_file(self, tmp_path, mock_perplexity_response):
        """Should create markdown file alongside PDF."""
        pdf_path = tmp_path / "Company.pdf"
        pdf_path.touch()

        summary = summarizer._parse_response(json.dumps(mock_perplexity_response))
        md_path = summarizer.write_summary(summary, pdf_path)

        assert md_path.exists()
        assert md_path.suffix == ".md"
        assert md_path.stem == "Company"

    def test_writes_formatted_content(self, tmp_path, mock_perplexity_response):
        """Should write properly formatted markdown."""
        pdf_path = tmp_path / "Company.pdf"
        pdf_path.touch()

        summary = summarizer._parse_response(json.dumps(mock_perplexity_response))
        md_path = summarizer.write_summary(summary, pdf_path)

        content = md_path.read_text()
        assert "# Acme Corp" in content
        assert "## Overview" in content


class TestCallPerplexity:
    """Tests for call_perplexity function."""

    def test_raises_error_when_openai_not_installed(self, monkeypatch):
        """Should raise SummaryError when openai not installed."""
        # Mock import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args):
            if name == "openai":
                raise ImportError("No module named 'openai'")
            return original_import(name, *args)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with pytest.raises(SummaryError) as exc_info:
            summarizer.call_perplexity("fake-key", "test text")

        assert "openai package not installed" in str(exc_info.value)

    def test_calls_perplexity_api(self, mock_perplexity_response):
        """Should call Perplexity API with correct parameters."""
        pytest.importorskip("openai")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(mock_perplexity_response)
        mock_client.chat.completions.create.return_value = mock_response

        with patch("openai.OpenAI", return_value=mock_client):
            result = summarizer.call_perplexity("pplx-test-key", "test ocr text")

        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "sonar-reasoning-pro"
        assert "test ocr text" in call_kwargs["messages"][0]["content"]
        # Verify search parameters (in extra_body for Perplexity)
        assert "extra_body" in call_kwargs
        assert "crunchbase.com" in call_kwargs["extra_body"]["search_domain_filter"]
        assert call_kwargs["extra_body"]["search_recency_filter"] == "month"

        # Verify result
        assert result.company.company_name == "Acme Corp"


class TestSummarize:
    """Tests for summarize function (main entry point)."""

    def test_full_pipeline(self, sample_screenshots_for_ocr, mock_perplexity_response, monkeypatch):
        """Should run full pipeline: OCR -> Perplexity -> Summary."""
        pytest.importorskip("openai")

        # Mock tesseract check
        monkeypatch.setattr(summarizer, "check_tesseract", lambda: True)

        # Mock pytesseract
        with patch("pytesseract.image_to_string", return_value="Acme Corp pitch deck"):
            # Mock Perplexity API
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_perplexity_response)
            mock_client.chat.completions.create.return_value = mock_response

            with patch("openai.OpenAI", return_value=mock_client):
                result = summarizer.summarize("pplx-test-key", sample_screenshots_for_ocr)

        assert isinstance(result, summarizer.StructuredSummary)
        assert result.company.company_name == "Acme Corp"
        assert len(result.funded_peers) == 2
