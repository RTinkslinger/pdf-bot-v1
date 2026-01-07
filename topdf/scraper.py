"""
DocSend Document Scraper
========================
Uses Playwright to scrape DocSend documents and capture page screenshots.

This module handles:
- Browser automation with Playwright (headless Chromium)
- DocSend URL validation
- Cookie consent dismissal
- Authentication flow delegation
- Page navigation and counting
- Screenshot capture for each page
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
    TimeoutError as PlaywrightTimeout,
)

from topdf.auth import AuthHandler, AuthType
from topdf.exceptions import (
    InvalidURLError,
    PageLoadError,
    ScrapingError,
    ScreenshotError,
    TimeoutError,
)


@dataclass
class ScrapeResult:
    """Result of scraping a DocSend document.

    Attributes:
        screenshots: List of PNG image bytes for each page
        page_title: The document's page title (used for filename extraction)
        page_count: Total number of pages in the document
    """
    screenshots: list[bytes]
    page_title: str
    page_count: int


class DocSendScraper:
    """Scrapes DocSend documents and captures page screenshots.

    This class handles the full scraping workflow:
    1. Launch headless browser
    2. Navigate to DocSend URL
    3. Dismiss cookie consent dialogs
    4. Handle authentication (email/passcode)
    5. Detect page count
    6. Capture screenshots of each page
    7. Clean up browser resources

    Usage:
        scraper = DocSendScraper(headless=True)
        result = await scraper.scrape(url, email="user@example.com")
    """

    # ==========================================================================
    # Configuration Constants
    # ==========================================================================

    # DocSend URL validation pattern
    URL_PATTERN = re.compile(r"^https?://(www\.)?docsend\.com/view/[\w-]+/?$")

    # Viewport size - matches typical slide dimensions for clean screenshots
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080

    # Timeouts (in milliseconds)
    NAVIGATION_TIMEOUT = 30000  # 30 seconds for page load
    PAGE_LOAD_TIMEOUT = 30000   # 30 seconds for content load
    SCREENSHOT_TIMEOUT = 10000  # 10 seconds per screenshot

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds between retries

    # ==========================================================================
    # Element Selectors
    # ==========================================================================

    # Selectors to find page count display (e.g., "1 of 14")
    PAGE_COUNT_SELECTORS = [
        '[data-testid="page-count"]',
        '.page-count',
        '.page-number',
        '[class*="page-indicator"]',
        '[class*="pageIndicator"]',
        '[class*="PageCount"]',
        '[class*="pageCount"]',
        'text=/\\d+\\s*(of|\\/)\\s*\\d+/',
        'text=/page\\s*\\d+/i',
    ]

    # Selectors for "Next" navigation button
    NEXT_BUTTON_SELECTORS = [
        '[data-testid="next-page"]',
        '[aria-label*="next" i]',
        '[aria-label*="Next" i]',
        'button[aria-label*="next" i]',
        '[class*="next"]',
        '[class*="Next"]',
        '.next-page',
        '.next-btn',
        'button:has-text("Next")',
        '[aria-label="Next page"]',
        'svg[class*="chevron-right"]',
        '[class*="right-arrow"]',
        '[class*="arrow-right"]',
    ]

    # Selectors for "Previous" navigation button
    PREV_BUTTON_SELECTORS = [
        '[data-testid="prev-page"]',
        '[aria-label*="previous" i]',
        '[aria-label*="Previous" i]',
        '[aria-label*="prev" i]',
        'button[aria-label*="previous" i]',
        '[class*="prev"]',
        '[class*="Prev"]',
        '.prev-page',
        '.prev-btn',
        'button:has-text("Previous")',
        '[aria-label="Previous page"]',
    ]

    # Selectors to detect document viewer container
    DOCUMENT_CONTAINER_SELECTORS = [
        '[data-testid="document-container"]',
        '.document-container',
        '.page-container',
        '.slide-container',
        '#document-viewer',
        '.viewer-container',
        '[class*="document"]',
        '[class*="viewer"]',
        '[class*="slide"]',
        '[class*="page-view"]',
        '[class*="pageView"]',
        'canvas',
        'img[class*="page"]',
        'img[class*="slide"]',
    ]

    # Selectors for cookie consent buttons to dismiss
    # NOTE: These are broad to handle various cookie consent implementations
    COOKIE_CONSENT_SELECTORS = [
        'button:has-text("Accept")',
        'button:has-text("Accept All")',
        'button:has-text("Accept Cookies")',
        'button:has-text("Allow")',
        'button:has-text("Allow All")',
        'button:has-text("I Accept")',
        'button:has-text("OK")',
        'button:has-text("Got it")',
        'button:has-text("Agree")',
        'button:has-text("Continue")',
        'button:has-text("Close")',
        '#onetrust-accept-btn-handler',
        '#accept-cookie-consent',
        '.onetrust-close-btn-handler',
        '[data-testid="cookie-accept"]',
        '[data-testid="accept-cookies"]',
        '.cookie-consent-accept',
        '.accept-cookies',
        '.cookie-accept',
        '.cc-accept',
        '.cc-btn',
        '[aria-label*="accept" i]',
        '[aria-label*="cookie" i]',
        '[aria-label*="consent" i]',
        '.cookie-banner button',
        '.cookie-notice button',
        '[class*="cookie"] button',
        '[class*="consent"] button',
        '[id*="cookie"] button',
    ]

    # ==========================================================================
    # Initialization
    # ==========================================================================

    def __init__(self, headless: bool = True, verbose: bool = False):
        """Initialize the scraper.

        Args:
            headless: If True, run browser without visible window.
                      Set to False for debugging.
            verbose: If True, print detailed progress messages.
        """
        self.headless = headless
        self.verbose = verbose

        # Browser instances (initialized in _launch_browser)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # Auth handler for email/passcode gates
        self._auth_handler = AuthHandler()

    # ==========================================================================
    # URL Validation
    # ==========================================================================

    def _validate_url(self, url: str) -> None:
        """Validate that URL is a valid DocSend link.

        Args:
            url: URL to validate

        Raises:
            InvalidURLError: If URL doesn't match DocSend pattern
        """
        if not self.URL_PATTERN.match(url):
            raise InvalidURLError(url)

    # ==========================================================================
    # Browser Management
    # ==========================================================================

    async def _launch_browser(self) -> None:
        """Launch Playwright browser with configured viewport and user agent."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
        )
        self._context = await self._browser.new_context(
            viewport={"width": self.VIEWPORT_WIDTH, "height": self.VIEWPORT_HEIGHT},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = await self._context.new_page()

    async def close(self) -> None:
        """Clean up browser resources.

        Safely closes page, context, browser, and playwright instances.
        Called automatically after scraping completes.
        """
        if self._page:
            try:
                await self._page.close()
            except Exception:
                pass
            self._page = None

        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    # ==========================================================================
    # Navigation
    # ==========================================================================

    async def _navigate(self, url: str) -> None:
        """Navigate to URL with retry logic.

        Args:
            url: URL to navigate to

        Raises:
            PageLoadError: If navigation fails after retries
            TimeoutError: If page load times out
        """
        if not self._page:
            raise ScrapingError(
                message="Browser not initialized",
                cause="Internal error",
                action="Report this issue",
            )

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                # Use domcontentloaded instead of networkidle
                # (networkidle never fires on DocSend due to continuous analytics)
                await self._page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.NAVIGATION_TIMEOUT,
                )
                # Wait for dynamic content to start loading
                await self._page.wait_for_timeout(2000)
                return
            except PlaywrightTimeout as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
            except Exception as e:
                raise PageLoadError(url, str(e))

        raise TimeoutError("Page navigation", self.NAVIGATION_TIMEOUT // 1000)

    async def _navigate_to_page(self, page_num: int) -> None:
        """Navigate to a specific page number.

        Args:
            page_num: Target page number (1-indexed)
        """
        if not self._page:
            return

        # Try Home key to go to first page
        try:
            await self._page.keyboard.press("Home")
            await self._page.wait_for_timeout(500)
        except Exception:
            pass

        # Click Previous until we reach page 1
        for _ in range(100):  # Safety limit
            prev_clicked = False
            for selector in self.PREV_BUTTON_SELECTORS:
                try:
                    locator = self._page.locator(selector).first
                    if await locator.is_visible(timeout=300):
                        if await locator.is_enabled():
                            await locator.click()
                            await self._page.wait_for_timeout(300)
                            prev_clicked = True
                            break
                        else:
                            # Button disabled = we're at page 1
                            prev_clicked = False
                            break
                except Exception:
                    continue

            if not prev_clicked:
                try:
                    await self._page.keyboard.press("ArrowLeft")
                    await self._page.wait_for_timeout(300)
                except Exception:
                    break
                break

        # Navigate forward to target page
        for _ in range(page_num - 1):
            await self._click_next()

    async def _click_next(self) -> bool:
        """Click next button to advance one page.

        Returns:
            True if successfully navigated, False if at last page
        """
        if not self._page:
            return False

        # Try clicking next buttons
        for selector in self.NEXT_BUTTON_SELECTORS:
            try:
                locator = self._page.locator(selector).first
                if await locator.is_visible(timeout=500):
                    if await locator.is_enabled():
                        await locator.click()
                        await self._page.wait_for_timeout(800)
                        return True
                    else:
                        return False  # Disabled = last page
            except Exception:
                continue

        # Fallback: keyboard navigation
        try:
            await self._page.keyboard.press("ArrowRight")
            await self._page.wait_for_timeout(800)
            return True
        except Exception:
            pass

        return False

    # ==========================================================================
    # Cookie Consent Handling
    # ==========================================================================

    async def _dismiss_cookie_consent(self) -> None:
        """Attempt to dismiss cookie consent banners.

        Tries each selector in COOKIE_CONSENT_SELECTORS until one succeeds.
        Exits after first successful click to avoid clicking multiple buttons.
        """
        if not self._page:
            return

        for selector in self.COOKIE_CONSENT_SELECTORS:
            try:
                locator = self._page.locator(selector).first
                if await locator.is_visible(timeout=1000):
                    await locator.click()
                    await self._page.wait_for_timeout(500)
                    if self.verbose:
                        print(f"Clicked cookie consent button: {selector}")
                    return  # Exit after first successful click
            except Exception:
                continue

    # ==========================================================================
    # Document Loading
    # ==========================================================================

    async def _wait_for_document(self) -> bool:
        """Wait for the document viewer to appear.

        Polls for document container, navigation elements, or images
        to confirm the document has loaded.

        Returns:
            True if document appears loaded, False otherwise
        """
        if not self._page:
            return False

        # Poll for up to 15 seconds
        for attempt in range(15):
            # Check for document container
            for selector in self.DOCUMENT_CONTAINER_SELECTORS:
                try:
                    if await self._page.locator(selector).first.is_visible(timeout=300):
                        if self.verbose:
                            print(f"Found document element: {selector}")
                        return True
                except Exception:
                    pass

            # Check for navigation elements (indicates document loaded)
            for selector in self.PAGE_COUNT_SELECTORS + self.NEXT_BUTTON_SELECTORS:
                try:
                    if await self._page.locator(selector).first.is_visible(timeout=300):
                        if self.verbose:
                            print(f"Found navigation element: {selector}")
                        return True
                except Exception:
                    pass

            # Check for any loaded images
            try:
                images = await self._page.locator('img').count()
                if images > 0:
                    if self.verbose:
                        print(f"Found {images} images on page")
                    await self._page.wait_for_timeout(1000)
                    return True
            except Exception:
                pass

            await self._page.wait_for_timeout(1000)

        if self.verbose:
            print("No specific document elements found, continuing anyway...")
        return True

    # ==========================================================================
    # Authentication
    # ==========================================================================

    async def _handle_auth(
        self,
        email: Optional[str],
        passcode: Optional[str],
    ) -> None:
        """Handle authentication if required.

        Detects auth type and delegates to appropriate handler.

        Args:
            email: Email address for email-gated documents
            passcode: Passcode for password-protected documents
        """
        if not self._page:
            return

        auth_type = await self._auth_handler.detect_auth_type(self._page)

        if self.verbose:
            print(f"Auth type detected: {auth_type.value}")

        if auth_type == AuthType.EMAIL:
            await self._auth_handler.handle_email_gate(self._page, email)
        elif auth_type == AuthType.PASSCODE:
            await self._auth_handler.handle_passcode_gate(self._page, email, passcode)

        # Wait for document to load after authentication
        if auth_type != AuthType.NONE:
            if self.verbose:
                print("Waiting for document to load after authentication...")

            # Use domcontentloaded (networkidle never fires due to analytics)
            try:
                await self._page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass
            await self._page.wait_for_timeout(3000)

            # Dismiss cookie consent that may appear after auth
            await self._dismiss_cookie_consent()

            # Wait for document viewer to appear
            if not await self._wait_for_document():
                if self.verbose:
                    print("Warning: Document container not found, continuing anyway...")

            await self._page.wait_for_timeout(2000)

    # ==========================================================================
    # Page Counting
    # ==========================================================================

    async def _get_page_count(self) -> int:
        """Get total number of pages in the document.

        Tries multiple strategies:
        1. Look for page count text (e.g., "1 of 14")
        2. Parse page content for count patterns
        3. Navigate through and count pages

        Returns:
            Total page count (minimum 1)
        """
        if not self._page:
            return 1

        # Strategy 1: Find page count from dedicated selectors
        for selector in self.PAGE_COUNT_SELECTORS:
            try:
                locator = self._page.locator(selector).first
                if await locator.is_visible(timeout=1000):
                    text = await locator.text_content()
                    if text:
                        match = re.search(r"(\d+)\s*(?:of|/)\s*(\d+)", text)
                        if match:
                            count = int(match.group(2))
                            if self.verbose:
                                print(f"Found page count from selector: {count}")
                            return count
            except Exception:
                continue

        # Strategy 2: Search page content for count patterns
        try:
            page_text = await self._page.content()
            matches = re.findall(r'(\d+)\s*(?:of|/)\s*(\d+)', page_text)
            for match in matches:
                total = int(match[1])
                if 1 < total <= 100:  # Reasonable range
                    if self.verbose:
                        print(f"Found page count from page content: {total}")
                    return total
        except Exception:
            pass

        if self.verbose:
            print("Could not find page count, will navigate to count pages...")

        # Strategy 3: Count by navigating through pages
        return await self._count_pages_by_navigation()

    async def _count_pages_by_navigation(self) -> int:
        """Count pages by navigating through the document.

        Navigates forward until reaching the last page,
        then returns to page 1.

        Returns:
            Total page count
        """
        if not self._page:
            return 1

        count = 1
        max_pages = 100  # Safety limit

        while count < max_pages:
            # Take screenshot for comparison
            try:
                current_screenshot = await self._page.screenshot(type="png")
            except Exception:
                current_screenshot = None

            # Try to advance
            if not await self._click_next():
                break

            # Verify page actually changed
            if current_screenshot:
                try:
                    new_screenshot = await self._page.screenshot(type="png")
                    if new_screenshot == current_screenshot:
                        break  # No change = last page
                except Exception:
                    pass

            count += 1
            if self.verbose:
                print(f"Counting pages: {count}...")

        if self.verbose:
            print(f"Total pages found: {count}")

        # Return to first page
        await self._navigate_to_page(1)
        return count

    # ==========================================================================
    # Screenshot Capture
    # ==========================================================================

    async def _capture_screenshot(self, page_num: int) -> bytes:
        """Capture screenshot of current page.

        Uses full viewport screenshot at 1920x1080 for consistent results.

        Args:
            page_num: Current page number (for error reporting)

        Returns:
            PNG image as bytes

        Raises:
            ScreenshotError: If capture fails after retries
        """
        if not self._page:
            raise ScreenshotError(page_num)

        for attempt in range(self.MAX_RETRIES):
            try:
                # Wait for content to render
                await self._page.wait_for_timeout(1500)

                # Full viewport screenshot (element-based is unreliable)
                return await self._page.screenshot(
                    type="png",
                    full_page=False,
                    timeout=self.SCREENSHOT_TIMEOUT,
                )
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)

        raise ScreenshotError(page_num)

    async def _get_page_title(self) -> str:
        """Get the browser page title.

        Returns:
            Page title string, or empty string on error
        """
        if not self._page:
            return ""
        try:
            return await self._page.title()
        except Exception:
            return ""

    async def _find_document_element(self) -> Optional[str]:
        """Find the document container element selector.

        Returns:
            First matching selector, or None if not found
        """
        if not self._page:
            return None

        for selector in self.DOCUMENT_CONTAINER_SELECTORS:
            try:
                locator = self._page.locator(selector).first
                if await locator.is_visible(timeout=1000):
                    return selector
            except Exception:
                continue
        return None

    # ==========================================================================
    # Main Scraping Method
    # ==========================================================================

    async def scrape(
        self,
        url: str,
        email: Optional[str] = None,
        passcode: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> ScrapeResult:
        """Scrape a DocSend document.

        Main entry point for scraping. Handles the full workflow:
        1. Validate URL
        2. Launch browser
        3. Navigate and handle auth
        4. Capture all pages
        5. Clean up

        Args:
            url: DocSend document URL
            email: Email for email-gated documents
            passcode: Passcode for password-protected documents
            progress_callback: Optional callback(current, total) for progress

        Returns:
            ScrapeResult containing screenshots and metadata

        Raises:
            InvalidURLError: If URL is not a valid DocSend link
            AuthenticationError: If authentication fails
            ScrapingError: If scraping fails
        """
        self._validate_url(url)

        try:
            # Initialize browser
            await self._launch_browser()

            # Load the document page
            await self._navigate(url)

            # Dismiss cookie consent before auth
            await self._dismiss_cookie_consent()

            # Handle authentication if required
            await self._handle_auth(email, passcode)

            # Dismiss cookie consent again (may reappear after auth)
            await self._dismiss_cookie_consent()

            # Get document metadata
            await self._page.wait_for_timeout(2000)
            page_title = await self._get_page_title()

            if self.verbose:
                print(f"Page title: {page_title}")

            # Determine page count
            page_count = await self._get_page_count()

            if self.verbose:
                print(f"Found {page_count} pages")

            # Capture all pages
            screenshots = []
            await self._navigate_to_page(1)

            for i in range(page_count):
                page_num = i + 1

                if progress_callback:
                    progress_callback(page_num, page_count)

                if self.verbose:
                    print(f"Capturing page {page_num}/{page_count}")

                screenshot = await self._capture_screenshot(page_num)
                screenshots.append(screenshot)

                if page_num < page_count:
                    await self._click_next()

            return ScrapeResult(
                screenshots=screenshots,
                page_title=page_title,
                page_count=page_count,
            )

        finally:
            await self.close()
