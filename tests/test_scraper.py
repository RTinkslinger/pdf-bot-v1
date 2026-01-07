"""Tests for scraper module."""

import pytest

from topdf.scraper import DocSendScraper, ScrapeResult
from topdf.exceptions import InvalidURLError


class TestScrapeResult:
    """Tests for ScrapeResult dataclass."""

    def test_scrape_result_creation(self):
        """Test creating a ScrapeResult."""
        result = ScrapeResult(
            screenshots=[b"img1", b"img2"],
            page_title="Test Title",
            page_count=2,
        )
        assert len(result.screenshots) == 2
        assert result.page_title == "Test Title"
        assert result.page_count == 2


class TestDocSendScraper:
    """Tests for DocSendScraper class."""

    @pytest.fixture
    def scraper(self) -> DocSendScraper:
        """Create a scraper instance."""
        return DocSendScraper(headless=True)

    def test_init_default_headless(self):
        """Test default headless mode."""
        scraper = DocSendScraper()
        assert scraper.headless is True

    def test_init_custom_headless(self):
        """Test custom headless mode."""
        scraper = DocSendScraper(headless=False)
        assert scraper.headless is False

    def test_init_verbose_mode(self):
        """Test verbose mode setting."""
        scraper = DocSendScraper(verbose=True)
        assert scraper.verbose is True

    def test_validate_url_valid(self, scraper: DocSendScraper, valid_docsend_urls):
        """Test URL validation with valid URLs."""
        for url in valid_docsend_urls:
            # Should not raise
            scraper._validate_url(url)

    def test_validate_url_invalid(self, scraper: DocSendScraper, invalid_urls):
        """Test URL validation with invalid URLs."""
        for url in invalid_urls:
            with pytest.raises(InvalidURLError):
                scraper._validate_url(url)

    def test_url_pattern_matches_valid_formats(self, scraper: DocSendScraper):
        """Test URL pattern with various valid formats."""
        valid_patterns = [
            "https://docsend.com/view/abc123",
            "https://www.docsend.com/view/abc123",
            "http://docsend.com/view/abc123",
            "https://docsend.com/view/abc-123",
            "https://docsend.com/view/ABC123/",
            "https://docsend.com/view/a1b2c3d4e5",
        ]
        for url in valid_patterns:
            assert scraper.URL_PATTERN.match(url) is not None

    def test_url_pattern_rejects_invalid_formats(self, scraper: DocSendScraper):
        """Test URL pattern rejects invalid formats."""
        invalid_patterns = [
            "https://docsend.com/",
            "https://docsend.com/abc123",
            "https://example.com/view/abc123",
            "https://docsend.com/view/",
            "docsend.com/view/abc123",
            "ftp://docsend.com/view/abc123",
        ]
        for url in invalid_patterns:
            assert scraper.URL_PATTERN.match(url) is None

    def test_viewport_dimensions(self, scraper: DocSendScraper):
        """Test viewport dimensions are set."""
        assert scraper.VIEWPORT_WIDTH == 1920
        assert scraper.VIEWPORT_HEIGHT == 1080

    def test_timeout_values(self, scraper: DocSendScraper):
        """Test timeout values are reasonable."""
        assert scraper.NAVIGATION_TIMEOUT >= 10000
        assert scraper.PAGE_LOAD_TIMEOUT >= 10000
        assert scraper.SCREENSHOT_TIMEOUT >= 5000

    def test_retry_settings(self, scraper: DocSendScraper):
        """Test retry settings are configured."""
        assert scraper.MAX_RETRIES >= 1
        assert scraper.RETRY_DELAY >= 0.5

    def test_selectors_defined(self, scraper: DocSendScraper):
        """Test that necessary selectors are defined."""
        assert len(scraper.PAGE_COUNT_SELECTORS) > 0
        assert len(scraper.NEXT_BUTTON_SELECTORS) > 0
        assert len(scraper.PREV_BUTTON_SELECTORS) > 0
        assert len(scraper.DOCUMENT_CONTAINER_SELECTORS) > 0

    def test_internal_state_initial(self, scraper: DocSendScraper):
        """Test initial internal state."""
        assert scraper._playwright is None
        assert scraper._browser is None
        assert scraper._context is None
        assert scraper._page is None

    @pytest.mark.asyncio
    async def test_close_handles_uninitialized(self, scraper: DocSendScraper):
        """Test close works when not initialized."""
        # Should not raise
        await scraper.close()

    @pytest.mark.asyncio
    async def test_scrape_validates_url(self, scraper: DocSendScraper):
        """Test that scrape validates URL first."""
        with pytest.raises(InvalidURLError):
            await scraper.scrape("https://example.com")


class TestScraperIntegration:
    """Integration tests for scraper (requires network)."""

    @pytest.mark.skip(reason="Requires real DocSend URL and network access")
    @pytest.mark.asyncio
    async def test_scrape_open_document(self):
        """Test scraping an open DocSend document."""
        scraper = DocSendScraper(headless=True)
        try:
            result = await scraper.scrape("https://docsend.com/view/REAL_URL")
            assert len(result.screenshots) > 0
            assert result.page_count > 0
        finally:
            await scraper.close()
