"""Tests for name extractor module."""

from pathlib import Path

import pytest

from topdf.name_extractor import NameExtractor


class TestNameExtractor:
    """Tests for NameExtractor class."""

    @pytest.fixture
    def extractor(self) -> NameExtractor:
        """Create a name extractor instance."""
        return NameExtractor(use_ocr=False)  # Disable OCR for unit tests

    def test_from_title_standard_format(self, extractor: NameExtractor):
        """Test parsing standard DocSend title format."""
        result = extractor._from_title("Acme Corp - Pitch Deck | DocSend")
        assert result == "Acme Corp"

    def test_from_title_simple_format(self, extractor: NameExtractor):
        """Test parsing simple title format."""
        result = extractor._from_title("Company Name | DocSend")
        assert result == "Company Name"

    def test_from_title_reverse_format(self, extractor: NameExtractor):
        """Test parsing reverse format (Deck - Company)."""
        result = extractor._from_title("Pitch Deck - TechCo | DocSend")
        assert result == "TechCo"

    def test_from_title_no_suffix(self, extractor: NameExtractor):
        """Test parsing title without DocSend suffix."""
        result = extractor._from_title("Simple Company Name")
        assert result == "Simple Company Name"

    def test_from_title_empty(self, extractor: NameExtractor):
        """Test that empty title returns None."""
        assert extractor._from_title("") is None
        assert extractor._from_title("   ") is None
        assert extractor._from_title(None) is None

    def test_from_title_various_formats(self, extractor: NameExtractor, sample_page_titles):
        """Test various title formats."""
        for title, expected in sample_page_titles:
            result = extractor._from_title(title)
            assert result == expected, f"Failed for title: {title}"

    def test_sanitize_filename_removes_invalid_chars(self, extractor: NameExtractor):
        """Test that invalid characters are removed."""
        result = extractor._sanitize_filename("Company/Name:With<Invalid>Chars")
        assert "/" not in result
        assert ":" not in result
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_filename_preserves_valid_chars(self, extractor: NameExtractor):
        """Test that valid characters are preserved."""
        result = extractor._sanitize_filename("Valid Company Name 123")
        assert result == "Valid Company Name 123"

    def test_sanitize_filename_strips_spaces(self, extractor: NameExtractor):
        """Test that leading/trailing spaces are stripped."""
        result = extractor._sanitize_filename("  Spaced Name  ")
        assert result == "Spaced Name"

    def test_sanitize_filename_collapses_spaces(self, extractor: NameExtractor):
        """Test that multiple spaces are collapsed."""
        result = extractor._sanitize_filename("Multiple   Spaces   Here")
        assert result == "Multiple Spaces Here"

    def test_sanitize_filename_strips_dots(self, extractor: NameExtractor):
        """Test that leading/trailing dots are stripped."""
        result = extractor._sanitize_filename("...Name...")
        assert result == "Name"

    def test_sanitize_filename_truncates_long_names(self, extractor: NameExtractor):
        """Test that very long names are truncated."""
        long_name = "A" * 200
        result = extractor._sanitize_filename(long_name)
        assert len(result) <= extractor.MAX_FILENAME_LENGTH

    def test_sanitize_filename_empty_returns_default(self, extractor: NameExtractor):
        """Test that empty result returns default."""
        result = extractor._sanitize_filename("///::")
        assert result == "DocSend Document"

    def test_sanitize_various_dirty_names(self, extractor: NameExtractor, dirty_filenames):
        """Test sanitization of various dirty filenames."""
        for dirty, expected in dirty_filenames:
            result = extractor._sanitize_filename(dirty)
            assert result == expected, f"Failed for: {dirty}"

    def test_extract_uses_title_first(self, extractor: NameExtractor):
        """Test that extract uses title as first choice."""
        result = extractor.extract(
            page_title="My Company | DocSend",
            first_screenshot=None,
            prompt_on_failure=False,
        )
        assert result == "My Company"

    def test_extract_returns_default_on_failure(self, extractor: NameExtractor):
        """Test that extract returns default when all methods fail."""
        result = extractor.extract(
            page_title=None,
            first_screenshot=None,
            prompt_on_failure=False,
        )
        assert result == "DocSend Document"

    def test_get_output_path_basic(self, extractor: NameExtractor, temp_dir: Path):
        """Test basic output path generation."""
        path = extractor.get_output_path("Test Company", str(temp_dir))
        assert path.name == "Test Company.pdf"
        assert path.parent == temp_dir

    def test_get_output_path_creates_directory(self, extractor: NameExtractor, temp_dir: Path):
        """Test that output path creates directory if needed."""
        new_dir = temp_dir / "subdir"
        path = extractor.get_output_path("Test", str(new_dir))
        assert new_dir.exists()

    def test_get_output_path_handles_duplicates(self, extractor: NameExtractor, temp_dir: Path):
        """Test that duplicate filenames are handled."""
        # Create first file
        first_path = temp_dir / "Test.pdf"
        first_path.write_text("dummy")

        # Get path should return unique name
        path = extractor.get_output_path("Test", str(temp_dir))
        assert path.name == "Test (1).pdf"

        # Create that file too
        path.write_text("dummy")

        # Should get next number
        path2 = extractor.get_output_path("Test", str(temp_dir))
        assert path2.name == "Test (2).pdf"

    def test_get_output_path_sanitizes_name(self, extractor: NameExtractor, temp_dir: Path):
        """Test that output path sanitizes the name."""
        path = extractor.get_output_path("Bad/Name:Here", str(temp_dir))
        assert "/" not in path.name
        assert ":" not in path.name
