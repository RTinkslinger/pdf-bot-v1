"""
topdf - DocSend to PDF Converter
================================
A CLI tool that converts DocSend document links to local PDF files.

Features:
- Headless browser automation with Playwright
- Email and passcode authentication support
- Full document capture with all pages
- Clean PDF output

Usage:
    topdf https://docsend.com/view/abc123 -n "My Document"
    topdf https://docsend.com/view/abc123 -n "Doc" -e user@example.com

Version: 1.0.1
"""

__version__ = "1.0.2"

from topdf.converter import Converter, ConversionResult
from topdf.exceptions import (
    TopdfError,
    InvalidURLError,
    AuthenticationError,
    ScrapingError,
    PDFBuildError,
    TimeoutError,
)

__all__ = [
    "__version__",
    "Converter",
    "ConversionResult",
    "TopdfError",
    "InvalidURLError",
    "AuthenticationError",
    "ScrapingError",
    "PDFBuildError",
    "TimeoutError",
]
