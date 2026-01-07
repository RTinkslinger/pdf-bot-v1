"""
Custom Exceptions for topdf
===========================
Defines the exception hierarchy for error handling.

All exceptions inherit from TopdfError, providing:
- Structured error messages
- Cause descriptions
- Suggested actions

Exception Hierarchy:
    TopdfError (base)
    ├── InvalidURLError
    ├── AuthenticationError
    │   ├── EmailRequiredError
    │   ├── PasscodeRequiredError
    │   └── InvalidCredentialsError
    ├── ScrapingError
    │   ├── PageLoadError
    │   └── ScreenshotError
    ├── PDFBuildError
    └── TimeoutError
"""


class TopdfError(Exception):
    """Base exception for all topdf errors.

    Provides structured error messages with cause and action suggestions.

    Attributes:
        message: Main error message
        cause: What caused the error
        action: Suggested action to resolve
    """

    def __init__(self, message: str, cause: str = "", action: str = ""):
        self.message = message
        self.cause = cause
        self.action = action
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with cause and action."""
        parts = [f"Error: {self.message}"]
        if self.cause:
            parts.append(f"Cause: {self.cause}")
        if self.action:
            parts.append(f"Action: {self.action}")
        return "\n".join(parts)


# =============================================================================
# URL Errors
# =============================================================================

class InvalidURLError(TopdfError):
    """Raised when URL is not a valid DocSend link."""

    def __init__(self, url: str):
        super().__init__(
            message=f"Invalid DocSend URL: {url}",
            cause="URL does not match DocSend format (https://docsend.com/view/...)",
            action="Provide a valid DocSend URL",
        )


# =============================================================================
# Authentication Errors
# =============================================================================

class AuthenticationError(TopdfError):
    """Base class for authentication-related errors."""
    pass


class EmailRequiredError(AuthenticationError):
    """Raised when email is required but not provided."""

    def __init__(self):
        super().__init__(
            message="Email required for this document",
            cause="This DocSend document requires email verification",
            action="Provide email with --email flag or when prompted",
        )


class PasscodeRequiredError(AuthenticationError):
    """Raised when passcode is required but not provided."""

    def __init__(self):
        super().__init__(
            message="Passcode required for this document",
            cause="This DocSend document requires a passcode",
            action="Provide passcode with --passcode flag or when prompted",
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided credentials are rejected."""

    def __init__(self):
        super().__init__(
            message="Invalid credentials",
            cause="The provided email or passcode was rejected",
            action="Check your credentials and try again",
        )


# =============================================================================
# Scraping Errors
# =============================================================================

class ScrapingError(TopdfError):
    """Base class for document scraping errors."""
    pass


class PageLoadError(ScrapingError):
    """Raised when a page fails to load."""

    def __init__(self, url: str, reason: str = ""):
        super().__init__(
            message="Failed to load DocSend page",
            cause=reason or "Page could not be loaded",
            action="Check your internet connection and try again",
        )


class ScreenshotError(ScrapingError):
    """Raised when screenshot capture fails."""

    def __init__(self, page_number: int):
        super().__init__(
            message=f"Failed to capture page {page_number}",
            cause="Screenshot capture failed after multiple attempts",
            action="Try again or check if the document is accessible",
        )


# =============================================================================
# PDF Errors
# =============================================================================

class PDFBuildError(TopdfError):
    """Raised when PDF generation fails."""

    def __init__(self, reason: str = ""):
        super().__init__(
            message="Failed to build PDF",
            cause=reason or "PDF generation failed",
            action="Try again or check if screenshots are valid",
        )


# =============================================================================
# Timeout Errors
# =============================================================================

class TimeoutError(TopdfError):
    """Raised when an operation times out."""

    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            message=f"{operation} timed out after {timeout_seconds} seconds",
            cause="The operation took too long to complete",
            action="Check your internet connection and try again",
        )
