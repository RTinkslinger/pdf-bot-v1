"""Tests for topdf CLI."""

import pytest
from click.testing import CliRunner

from topdf.cli import topdf, validate_url
from topdf.exceptions import InvalidURLError


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_urls(self, valid_docsend_urls: list[str]):
        """Test that valid DocSend URLs are accepted."""
        for url in valid_docsend_urls:
            result = validate_url(url)
            assert result == url

    def test_invalid_urls(self, invalid_urls: list[str]):
        """Test that invalid URLs are rejected."""
        for url in invalid_urls:
            with pytest.raises(InvalidURLError):
                validate_url(url)


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    def test_help_flag(self, runner: CliRunner):
        """Test --help shows usage information."""
        result = runner.invoke(topdf, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Convert a DocSend document to PDF" in result.output

    def test_version_flag(self, runner: CliRunner):
        """Test --version shows version."""
        result = runner.invoke(topdf, ["--version"])
        assert result.exit_code == 0
        assert "1.0.1" in result.output

    def test_missing_url(self, runner: CliRunner):
        """Test error when URL is not provided."""
        result = runner.invoke(topdf, [])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "URL" in result.output

    def test_invalid_url_error(self, runner: CliRunner):
        """Test error message for invalid URL."""
        result = runner.invoke(topdf, ["https://example.com", "--name", "Test"])
        assert result.exit_code != 0
        assert "Invalid DocSend URL" in result.output

    def test_options_parsed(self, runner: CliRunner):
        """Test that all options are parsed correctly."""
        # This will fail at conversion (no real DocSend), but we're testing parsing
        result = runner.invoke(
            topdf,
            [
                "https://docsend.com/view/test123",
                "--email", "test@example.com",
                "--passcode", "secret",
                "--name", "Custom Name",
                "--output", "/tmp/output",
                "--verbose",
            ],
        )
        # It should fail at scraping, not at argument parsing
        # The error should not be about invalid arguments
        assert "invalid option" not in result.output.lower()
        assert "unrecognized" not in result.output.lower()

    def test_short_options(self, runner: CliRunner):
        """Test short option flags work."""
        result = runner.invoke(
            topdf,
            [
                "https://docsend.com/view/test123",
                "-e", "test@example.com",
                "-p", "secret",
                "-n", "Name",
                "-o", "/tmp",
                "-v",
            ],
        )
        # Should not fail on argument parsing
        assert "invalid option" not in result.output.lower()

    def test_help_shows_examples(self, runner: CliRunner):
        """Test that help includes usage examples."""
        result = runner.invoke(topdf, ["--help"])
        assert "Examples:" in result.output or "example" in result.output.lower()
        assert "docsend.com/view" in result.output

    def test_help_shows_all_options(self, runner: CliRunner):
        """Test that help shows all options."""
        result = runner.invoke(topdf, ["--help"])
        assert "--email" in result.output
        assert "--passcode" in result.output
        assert "--name" in result.output
        assert "--output" in result.output
        assert "--verbose" in result.output
        assert "--version" in result.output
