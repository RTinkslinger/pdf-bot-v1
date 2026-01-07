"""Tests for authentication module."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from topdf.auth import AuthHandler, AuthType
from topdf.exceptions import (
    EmailRequiredError,
    PasscodeRequiredError,
)


class TestAuthType:
    """Tests for AuthType enum."""

    def test_auth_type_values(self):
        """Test AuthType enum values."""
        assert AuthType.NONE.value == "none"
        assert AuthType.EMAIL.value == "email"
        assert AuthType.PASSCODE.value == "passcode"

    def test_auth_type_members(self):
        """Test AuthType has expected members."""
        assert hasattr(AuthType, "NONE")
        assert hasattr(AuthType, "EMAIL")
        assert hasattr(AuthType, "PASSCODE")


class TestAuthHandler:
    """Tests for AuthHandler class."""

    @pytest.fixture
    def handler(self) -> AuthHandler:
        """Create an auth handler instance."""
        return AuthHandler(timeout=5000)

    def test_init_default_timeout(self):
        """Test default timeout value."""
        handler = AuthHandler()
        assert handler.timeout == 10000

    def test_init_custom_timeout(self):
        """Test custom timeout value."""
        handler = AuthHandler(timeout=5000)
        assert handler.timeout == 5000

    def test_email_input_selectors_defined(self, handler: AuthHandler):
        """Test that email input selectors are defined."""
        assert len(handler.EMAIL_INPUT_SELECTORS) > 0
        assert any("email" in s.lower() for s in handler.EMAIL_INPUT_SELECTORS)

    def test_passcode_input_selectors_defined(self, handler: AuthHandler):
        """Test that passcode input selectors are defined."""
        assert len(handler.PASSCODE_INPUT_SELECTORS) > 0
        assert any(
            "password" in s.lower() or "passcode" in s.lower()
            for s in handler.PASSCODE_INPUT_SELECTORS
        )

    def test_submit_button_selectors_defined(self, handler: AuthHandler):
        """Test that submit button selectors are defined."""
        assert len(handler.SUBMIT_BUTTON_SELECTORS) > 0
        assert any("submit" in s.lower() for s in handler.SUBMIT_BUTTON_SELECTORS)

    @pytest.mark.asyncio
    async def test_detect_auth_type_none(self, handler: AuthHandler):
        """Test detecting no auth requirement."""
        # Create mock page where no auth elements are visible
        page = MagicMock()
        locator = MagicMock()
        locator.first = MagicMock()
        locator.first.is_visible = AsyncMock(side_effect=Exception("Not found"))
        page.locator = MagicMock(return_value=locator)

        auth_type = await handler.detect_auth_type(page)
        assert auth_type == AuthType.NONE

    @pytest.mark.asyncio
    async def test_handle_email_gate_requires_email(self, handler: AuthHandler):
        """Test that email gate requires email parameter."""
        page = MagicMock()

        with pytest.raises(EmailRequiredError):
            await handler.handle_email_gate(page, email=None)

    @pytest.mark.asyncio
    async def test_handle_passcode_gate_requires_email(self, handler: AuthHandler):
        """Test that passcode gate requires email parameter."""
        page = MagicMock()

        with pytest.raises(EmailRequiredError):
            await handler.handle_passcode_gate(page, email=None, passcode="secret")

    @pytest.mark.asyncio
    async def test_handle_passcode_gate_requires_passcode(self, handler: AuthHandler):
        """Test that passcode gate requires passcode parameter."""
        page = MagicMock()

        with pytest.raises(PasscodeRequiredError):
            await handler.handle_passcode_gate(page, email="test@example.com", passcode=None)

    @pytest.mark.asyncio
    async def test_find_and_fill_returns_false_on_failure(self, handler: AuthHandler):
        """Test that _find_and_fill returns False when no element found."""
        page = MagicMock()
        locator = MagicMock()
        locator.first = MagicMock()
        locator.first.is_visible = AsyncMock(side_effect=Exception("Not found"))
        page.locator = MagicMock(return_value=locator)

        result = await handler._find_and_fill(
            page,
            ["input.nonexistent"],
            "value",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_click_submit_returns_false_on_failure(self, handler: AuthHandler):
        """Test that _click_submit returns False when no button found."""
        page = MagicMock()
        locator = MagicMock()
        locator.first = MagicMock()
        locator.first.is_visible = AsyncMock(side_effect=Exception("Not found"))
        page.locator = MagicMock(return_value=locator)

        result = await handler._click_submit(page)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_for_error_returns_false_when_no_error(self, handler: AuthHandler):
        """Test that _check_for_error returns False when no error visible."""
        page = MagicMock()
        locator = MagicMock()
        locator.first = MagicMock()
        locator.first.is_visible = AsyncMock(side_effect=Exception("Not found"))
        page.locator = MagicMock(return_value=locator)

        result = await handler._check_for_error(page)
        assert result is False
