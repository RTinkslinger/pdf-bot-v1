"""Pytest fixtures for topdf tests."""

import io
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from PIL import Image


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_screenshot() -> bytes:
    """Create a sample PNG screenshot for testing."""
    # Create a simple test image
    img = Image.new("RGB", (1920, 1080), color=(255, 255, 255))

    # Add some content to make it more realistic
    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 100, 1820, 980], outline=(0, 0, 0), width=2)
    draw.text((960, 540), "Test Slide", fill=(0, 0, 0), anchor="mm")

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def sample_screenshots(sample_screenshot: bytes) -> list[bytes]:
    """Create multiple sample screenshots."""
    screenshots = []
    for i in range(3):
        img = Image.new("RGB", (1920, 1080), color=(255, 255, 255))
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 1820, 980], outline=(0, 0, 0), width=2)
        draw.text((960, 540), f"Test Slide {i + 1}", fill=(0, 0, 0), anchor="mm")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        screenshots.append(buffer.getvalue())
    return screenshots


@pytest.fixture
def valid_docsend_urls() -> list[str]:
    """List of valid DocSend URL formats."""
    return [
        "https://docsend.com/view/abc123",
        "https://www.docsend.com/view/abc123",
        "http://docsend.com/view/abc123",
        "https://docsend.com/view/abc-123-def",
        "https://docsend.com/view/ABC123/",
    ]


@pytest.fixture
def invalid_urls() -> list[str]:
    """List of invalid URLs."""
    return [
        "https://example.com",
        "https://docsend.com/",
        "https://docsend.com/abc123",
        "https://google.com/view/abc123",
        "not-a-url",
        "",
    ]


@pytest.fixture
def sample_page_titles() -> list[tuple[str, str]]:
    """Sample page titles and expected company names."""
    return [
        ("Acme Corp - Pitch Deck | DocSend", "Acme Corp"),
        ("Startup Inc - Pitch Deck | DocSend", "Startup Inc"),
        ("Company XYZ | DocSend", "Company XYZ"),
        ("Pitch Deck - TechCo | DocSend", "TechCo"),
        ("Simple Name", "Simple Name"),
        ("Name With Suffix | Powered by DocSend", "Name With Suffix"),
    ]


@pytest.fixture
def dirty_filenames() -> list[tuple[str, str]]:
    """Dirty filenames and their sanitized versions."""
    return [
        ("Company/Inc", "CompanyInc"),
        ("Name: With Colon", "Name With Colon"),
        ("Name\\With\\Slashes", "NameWithSlashes"),
        ("Name<With>Brackets", "NameWithBrackets"),
        ('Name"With"Quotes', "NameWithQuotes"),
        ("Name?With?Questions", "NameWithQuestions"),
        ("Name*With*Stars", "NameWithStars"),
        ("  Spaces  Around  ", "Spaces Around"),
        ("...dots...", "dots"),
    ]
