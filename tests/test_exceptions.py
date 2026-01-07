"""Tests for topdf exceptions."""

import pytest

from topdf.exceptions import (
    TopdfError,
    InvalidURLError,
    AuthenticationError,
    EmailRequiredError,
    PasscodeRequiredError,
    InvalidCredentialsError,
    ScrapingError,
    PageLoadError,
    ScreenshotError,
    PDFBuildError,
    TimeoutError,
)


class TestTopdfError:
    """Tests for base TopdfError."""

    def test_basic_error(self):
        """Test basic error with message only."""
        error = TopdfError("Something went wrong")
        assert "Something went wrong" in str(error)

    def test_error_with_cause_and_action(self):
        """Test error with cause and action."""
        error = TopdfError(
            message="Failed to connect",
            cause="Network unreachable",
            action="Check your internet connection",
        )
        error_str = str(error)
        assert "Failed to connect" in error_str
        assert "Network unreachable" in error_str
        assert "Check your internet connection" in error_str

    def test_error_attributes(self):
        """Test that error attributes are accessible."""
        error = TopdfError("msg", "cause", "action")
        assert error.message == "msg"
        assert error.cause == "cause"
        assert error.action == "action"


class TestInvalidURLError:
    """Tests for InvalidURLError."""

    def test_invalid_url_message(self):
        """Test that invalid URL is included in message."""
        error = InvalidURLError("https://example.com")
        assert "https://example.com" in str(error)
        assert "Invalid DocSend URL" in str(error)

    def test_provides_action(self):
        """Test that error provides helpful action."""
        error = InvalidURLError("bad-url")
        assert "docsend.com/view" in str(error).lower()


class TestAuthenticationErrors:
    """Tests for authentication-related errors."""

    def test_email_required_error(self):
        """Test EmailRequiredError message."""
        error = EmailRequiredError()
        error_str = str(error)
        assert "email" in error_str.lower()
        assert "--email" in error_str or "email" in error_str.lower()

    def test_passcode_required_error(self):
        """Test PasscodeRequiredError message."""
        error = PasscodeRequiredError()
        error_str = str(error)
        assert "passcode" in error_str.lower()

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError message."""
        error = InvalidCredentialsError()
        error_str = str(error)
        assert "invalid" in error_str.lower() or "rejected" in error_str.lower()

    def test_inheritance(self):
        """Test that auth errors inherit from AuthenticationError."""
        assert isinstance(EmailRequiredError(), AuthenticationError)
        assert isinstance(PasscodeRequiredError(), AuthenticationError)
        assert isinstance(InvalidCredentialsError(), AuthenticationError)
        assert isinstance(AuthenticationError("test"), TopdfError)


class TestScrapingErrors:
    """Tests for scraping-related errors."""

    def test_page_load_error(self):
        """Test PageLoadError message."""
        error = PageLoadError("https://docsend.com/view/abc", "Connection refused")
        error_str = str(error)
        assert "load" in error_str.lower() or "failed" in error_str.lower()

    def test_screenshot_error(self):
        """Test ScreenshotError includes page number."""
        error = ScreenshotError(5)
        error_str = str(error)
        assert "5" in error_str
        assert "capture" in error_str.lower() or "screenshot" in error_str.lower()

    def test_inheritance(self):
        """Test that scraping errors inherit correctly."""
        assert isinstance(PageLoadError("url", "reason"), ScrapingError)
        assert isinstance(ScreenshotError(1), ScrapingError)
        assert isinstance(ScrapingError("test", "", ""), TopdfError)


class TestPDFBuildError:
    """Tests for PDFBuildError."""

    def test_basic_error(self):
        """Test basic PDFBuildError."""
        error = PDFBuildError()
        assert "pdf" in str(error).lower()

    def test_with_reason(self):
        """Test PDFBuildError with specific reason."""
        error = PDFBuildError("Invalid image format")
        assert "Invalid image format" in str(error)


class TestTimeoutError:
    """Tests for TimeoutError."""

    def test_timeout_includes_operation_and_duration(self):
        """Test that timeout error includes operation and duration."""
        error = TimeoutError("Page navigation", 30)
        error_str = str(error)
        assert "navigation" in error_str.lower()
        assert "30" in error_str


class TestExceptionHierarchy:
    """Tests for the exception hierarchy."""

    def test_all_errors_inherit_from_base(self):
        """Test that all custom errors inherit from TopdfError."""
        errors = [
            InvalidURLError("url"),
            AuthenticationError("msg", "", ""),
            EmailRequiredError(),
            PasscodeRequiredError(),
            InvalidCredentialsError(),
            ScrapingError("msg", "", ""),
            PageLoadError("url", "reason"),
            ScreenshotError(1),
            PDFBuildError(),
            TimeoutError("op", 10),
        ]
        for error in errors:
            assert isinstance(error, TopdfError)
            assert isinstance(error, Exception)

    def test_can_catch_by_base_class(self):
        """Test that errors can be caught by base class."""
        with pytest.raises(TopdfError):
            raise InvalidURLError("test")

        with pytest.raises(AuthenticationError):
            raise EmailRequiredError()

        with pytest.raises(ScrapingError):
            raise ScreenshotError(1)
