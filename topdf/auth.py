"""
Authentication Handler for DocSend
==================================
Handles email and passcode authentication gates on DocSend documents.

This module detects and handles:
- Email-gated documents (require email to view)
- Passcode-protected documents (require email + passcode)
"""

from enum import Enum
from typing import Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from topdf.exceptions import (
    AuthenticationError,
    EmailRequiredError,
    InvalidCredentialsError,
    PasscodeRequiredError,
)


class AuthType(Enum):
    """Types of authentication gates on DocSend documents."""
    NONE = "none"          # No authentication required
    EMAIL = "email"        # Email-only gate
    PASSCODE = "passcode"  # Email + passcode gate


class AuthHandler:
    """Handles DocSend authentication flows.

    Detects authentication requirements and submits credentials.

    Usage:
        handler = AuthHandler()
        auth_type = await handler.detect_auth_type(page)
        if auth_type == AuthType.EMAIL:
            await handler.handle_email_gate(page, email)
    """

    # ==========================================================================
    # Element Selectors
    # ==========================================================================

    # Email input field selectors
    EMAIL_INPUT_SELECTORS = [
        'input[type="email"]',
        'input[name="email"]',
        'input[name="link_auth_form[email]"]',
        'input[placeholder*="email" i]',
        'input[data-testid="email-input"]',
        '#email',
        '#link_auth_form_email',
        'input[autocomplete="email"]',
    ]

    # Passcode input field selectors
    PASSCODE_INPUT_SELECTORS = [
        'input[type="password"]',
        'input[name="passcode"]',
        'input[name="password"]',
        'input[name="link_auth_form[passcode]"]',
        'input[placeholder*="passcode" i]',
        'input[data-testid="passcode-input"]',
        '#passcode',
        '#link_auth_form_passcode',
    ]

    # Submit button selectors
    SUBMIT_BUTTON_SELECTORS = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Continue")',
        'button:has-text("Submit")',
        'button:has-text("View")',
        'button:has-text("View Document")',
        'button:has-text("Access")',
        'button:has-text("Enter")',
        '[data-testid="submit-button"]',
        '.submit-button',
        'form button',
    ]

    # Email gate container selectors
    EMAIL_GATE_SELECTORS = [
        '[data-testid="email-gate"]',
        'form:has(input[type="email"])',
        '.email-capture',
        '.email-gate',
        '.visitor-email-capture',
        '#new_link_auth_form',
    ]

    # Passcode gate container selectors
    PASSCODE_GATE_SELECTORS = [
        '[data-testid="passcode-gate"]',
        'form:has(input[type="password"])',
        '.passcode-gate',
    ]

    # Error message selectors
    AUTH_ERROR_SELECTORS = [
        '.error-message',
        '[data-testid="auth-error"]',
        '.alert-error',
        '.alert-danger',
        '.form-error',
        'text=invalid',
        'text=incorrect',
        'text=denied',
    ]

    # ==========================================================================
    # Initialization
    # ==========================================================================

    def __init__(self, timeout: int = 10000):
        """Initialize auth handler.

        Args:
            timeout: Timeout in milliseconds for auth operations
        """
        self.timeout = timeout

    # ==========================================================================
    # Auth Type Detection
    # ==========================================================================

    async def detect_auth_type(self, page: Page) -> AuthType:
        """Detect which type of authentication is required.

        Checks for passcode gate first (more specific), then email gate.

        Args:
            page: Playwright page object

        Returns:
            AuthType indicating what authentication is needed
        """
        # Check for passcode gate first (more specific than email)
        for selector in self.PASSCODE_GATE_SELECTORS:
            try:
                if await page.locator(selector).first.is_visible(timeout=1000):
                    return AuthType.PASSCODE
            except (PlaywrightTimeout, Exception):
                continue

        # Check for passcode input field
        for selector in self.PASSCODE_INPUT_SELECTORS:
            try:
                if await page.locator(selector).first.is_visible(timeout=1000):
                    return AuthType.PASSCODE
            except (PlaywrightTimeout, Exception):
                continue

        # Check for email gate
        for selector in self.EMAIL_GATE_SELECTORS:
            try:
                if await page.locator(selector).first.is_visible(timeout=1000):
                    return AuthType.EMAIL
            except (PlaywrightTimeout, Exception):
                continue

        # Check for email input field
        for selector in self.EMAIL_INPUT_SELECTORS:
            try:
                if await page.locator(selector).first.is_visible(timeout=1000):
                    return AuthType.EMAIL
            except (PlaywrightTimeout, Exception):
                continue

        return AuthType.NONE

    # ==========================================================================
    # Form Interaction Helpers
    # ==========================================================================

    async def _find_and_fill(
        self, page: Page, selectors: list[str], value: str
    ) -> bool:
        """Find an input field and fill it with a value.

        Args:
            page: Playwright page object
            selectors: List of CSS selectors to try
            value: Value to enter into the field

        Returns:
            True if field was found and filled, False otherwise
        """
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if await locator.is_visible(timeout=2000):
                    await locator.click()  # Focus the field
                    await page.wait_for_timeout(200)
                    await locator.fill(value)
                    await page.wait_for_timeout(300)
                    return True
            except Exception:
                continue
        return False

    async def _click_submit(self, page: Page) -> bool:
        """Find and click the submit button.

        Args:
            page: Playwright page object

        Returns:
            True if button was found and clicked, False otherwise
        """
        for selector in self.SUBMIT_BUTTON_SELECTORS:
            try:
                locator = page.locator(selector).first
                if await locator.is_visible(timeout=2000):
                    await locator.click()
                    return True
            except Exception:
                continue
        return False

    async def _check_for_error(self, page: Page) -> bool:
        """Check if an authentication error message is displayed.

        Args:
            page: Playwright page object

        Returns:
            True if error message found, False otherwise
        """
        for selector in self.AUTH_ERROR_SELECTORS:
            try:
                if await page.locator(selector).first.is_visible(timeout=1000):
                    return True
            except Exception:
                continue
        return False

    async def _wait_for_auth_success(self, page: Page) -> bool:
        """Wait for authentication to complete successfully.

        Waits for page load, then checks if we're still on an auth page.

        Args:
            page: Playwright page object

        Returns:
            True if authentication succeeded, False otherwise
        """
        try:
            # Wait for page to finish loading
            await page.wait_for_load_state("domcontentloaded", timeout=self.timeout)

            # Allow time for redirects or page updates
            await page.wait_for_timeout(3000)

            # Check if still on auth page
            auth_type = await self.detect_auth_type(page)
            if auth_type != AuthType.NONE:
                # Still showing auth form - check for error
                if await self._check_for_error(page):
                    return False
                # Give more time (slow loading)
                await page.wait_for_timeout(5000)
                auth_type = await self.detect_auth_type(page)
                return auth_type == AuthType.NONE

            return True

        except PlaywrightTimeout:
            # Timeout might still mean success if page navigated
            await page.wait_for_timeout(2000)
            auth_type = await self.detect_auth_type(page)
            return auth_type == AuthType.NONE

    # ==========================================================================
    # Authentication Handlers
    # ==========================================================================

    async def handle_email_gate(
        self,
        page: Page,
        email: Optional[str],
    ) -> bool:
        """Handle email-only authentication gate.

        Args:
            page: Playwright page object
            email: Email address to submit

        Returns:
            True if authentication succeeded

        Raises:
            EmailRequiredError: If email is not provided
            InvalidCredentialsError: If email was rejected
            AuthenticationError: If submission failed
        """
        if not email:
            raise EmailRequiredError()

        # Fill email field
        if not await self._find_and_fill(page, self.EMAIL_INPUT_SELECTORS, email):
            raise AuthenticationError(
                message="Could not find email input field",
                cause="DocSend page structure may have changed",
                action="Try again or report this issue",
            )

        # Submit the form
        if not await self._click_submit(page):
            await page.keyboard.press("Enter")  # Fallback

        # Wait for result
        if not await self._wait_for_auth_success(page):
            if await self._check_for_error(page):
                raise InvalidCredentialsError()
            raise AuthenticationError(
                message="Email submission failed",
                cause="Unknown error during email verification",
                action="Check your email and try again",
            )

        return True

    async def handle_passcode_gate(
        self,
        page: Page,
        email: Optional[str],
        passcode: Optional[str],
    ) -> bool:
        """Handle email + passcode authentication gate.

        Args:
            page: Playwright page object
            email: Email address
            passcode: Document passcode

        Returns:
            True if authentication succeeded

        Raises:
            EmailRequiredError: If email is not provided
            PasscodeRequiredError: If passcode is not provided
            InvalidCredentialsError: If credentials were rejected
            AuthenticationError: If submission failed
        """
        if not email:
            raise EmailRequiredError()
        if not passcode:
            raise PasscodeRequiredError()

        # Fill email if field is visible
        await self._find_and_fill(page, self.EMAIL_INPUT_SELECTORS, email)

        # Fill passcode (required)
        if not await self._find_and_fill(page, self.PASSCODE_INPUT_SELECTORS, passcode):
            raise AuthenticationError(
                message="Could not find passcode input field",
                cause="DocSend page structure may have changed",
                action="Try again or report this issue",
            )

        # Submit the form
        if not await self._click_submit(page):
            await page.keyboard.press("Enter")  # Fallback

        # Wait for result
        if not await self._wait_for_auth_success(page):
            if await self._check_for_error(page):
                raise InvalidCredentialsError()
            raise AuthenticationError(
                message="Passcode submission failed",
                cause="Unknown error during passcode verification",
                action="Check your credentials and try again",
            )

        return True
