"""Company name extraction from DocSend documents."""

import io
import re
from pathlib import Path
from typing import Optional

from PIL import Image

from topdf.exceptions import TopdfError


class NameExtractor:
    """Extracts company name for PDF filename."""

    # Maximum filename length
    MAX_FILENAME_LENGTH = 100

    # Characters invalid in filenames
    INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

    # Common DocSend title suffixes to remove
    TITLE_SUFFIXES = [
        r"\s*\|\s*DocSend\s*$",
        r"\s*-\s*DocSend\s*$",
        r"\s*\|\s*Powered by DocSend\s*$",
        r"\s*on\s+DocSend\s*$",
        r"\s*DocSend\s*$",
    ]

    # Common patterns to extract company name from title
    TITLE_PATTERNS = [
        # "Company Name - Pitch Deck | DocSend"
        r"^(.+?)\s*[-–—]\s*(?:Pitch\s*Deck|Deck|Presentation|Series\s*[A-Z])",
        # "Pitch Deck - Company Name | DocSend"
        r"(?:Pitch\s*Deck|Deck|Presentation|Series\s*[A-Z])\s*[-–—]\s*(.+)",
        # Just the company name (after removing suffix)
        r"^(.+)$",
    ]

    # Titles to reject (not useful for naming)
    REJECT_TITLES = [
        "docsend",
        "document",
        "untitled",
        "view document",
        "loading",
    ]

    # OCR text patterns to reject (DocSend UI elements)
    OCR_REJECT_PATTERNS = [
        r"requests?\s+your\s+action",
        r"continue\s+to\s+view",
        r"enter\s+your\s+email",
        r"verify\s+your\s+email",
        r"please\s+enter",
        r"click\s+here",
        r"powered\s+by",
        r"confidential",
        r"private\s+&\s+confidential",
        r"all\s+rights\s+reserved",
        r"copyright\s+\d{4}",
        r"©\s*\d{4}",
    ]

    def __init__(self, use_ocr: bool = True):
        """Initialize name extractor.

        Args:
            use_ocr: Whether to use OCR as fallback
        """
        self.use_ocr = use_ocr
        self._tesseract_available: Optional[bool] = None

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available.

        Returns:
            True if Tesseract is available
        """
        if self._tesseract_available is not None:
            return self._tesseract_available

        try:
            import pytesseract
            # Try to run tesseract to check if it's installed
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except Exception:
            self._tesseract_available = False

        return self._tesseract_available

    def _from_title(self, title: str) -> Optional[str]:
        """Parse company name from DocSend page title.

        Args:
            title: Page title string

        Returns:
            Extracted company name, or None if not found
        """
        if not title or not title.strip():
            return None

        # Remove DocSend suffixes
        cleaned = title.strip()
        for suffix_pattern in self.TITLE_SUFFIXES:
            cleaned = re.sub(suffix_pattern, "", cleaned, flags=re.IGNORECASE)

        cleaned = cleaned.strip()
        if not cleaned:
            return None

        # Reject useless titles
        if cleaned.lower() in self.REJECT_TITLES:
            return None

        # Try to extract company name using patterns
        for pattern in self.TITLE_PATTERNS:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Also reject if extracted name is useless
                if name and len(name) >= 2 and name.lower() not in self.REJECT_TITLES:
                    return name

        # If no pattern matched, use the cleaned title if it's not a reject
        if cleaned and cleaned.lower() not in self.REJECT_TITLES:
            return cleaned

        return None

    def _from_ocr(self, screenshot: bytes) -> Optional[str]:
        """Extract company name via OCR on first slide.

        Args:
            screenshot: PNG image bytes

        Returns:
            Extracted company name, or None if not found
        """
        if not self.use_ocr or not self._check_tesseract():
            return None

        try:
            import pytesseract

            # Load image
            image = Image.open(io.BytesIO(screenshot))

            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Run OCR
            text = pytesseract.image_to_string(image)

            # Try to extract company name from OCR text
            # Look for the first line that looks like a company name
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            for line in lines[:5]:  # Check first 5 non-empty lines
                # Skip very short or very long lines
                if len(line) < 2 or len(line) > 60:
                    continue

                # Skip lines that look like dates, numbers, or common phrases
                if re.match(r"^[\d\s/.-]+$", line):
                    continue
                if re.match(r"^(confidential|private|draft|page\s*\d+)$", line, re.IGNORECASE):
                    continue

                # Skip lines matching DocSend UI patterns
                is_reject = False
                for pattern in self.OCR_REJECT_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        is_reject = True
                        break
                if is_reject:
                    continue

                # This might be the company name
                return line

            return None

        except Exception:
            return None

    def _sanitize_filename(self, name: str) -> str:
        """Remove invalid filesystem characters from name.

        Args:
            name: Raw name string

        Returns:
            Sanitized filename-safe string
        """
        # Remove invalid characters
        sanitized = re.sub(self.INVALID_CHARS, "", name)

        # Replace multiple spaces/underscores with single space
        sanitized = re.sub(r"[\s_]+", " ", sanitized)

        # Strip leading/trailing whitespace and dots
        sanitized = sanitized.strip(" .")

        # Truncate if too long
        if len(sanitized) > self.MAX_FILENAME_LENGTH:
            sanitized = sanitized[: self.MAX_FILENAME_LENGTH].strip()

        # If empty after sanitization, use default
        if not sanitized:
            sanitized = "DocSend Document"

        return sanitized

    def _prompt_user(self) -> str:
        """Ask user for company name.

        Returns:
            User-provided company name
        """
        try:
            from rich.console import Console
            from rich.prompt import Prompt

            console = Console()
            console.print(
                "\n[yellow]Could not automatically detect company name.[/yellow]"
            )
            name = Prompt.ask("Please enter the company/document name")
            return name.strip() if name else "DocSend Document"
        except Exception:
            # Fallback to basic input
            print("\nCould not automatically detect company name.")
            name = input("Please enter the company/document name: ")
            return name.strip() if name else "DocSend Document"

    def _get_unique_filename(self, base_path: Path) -> Path:
        """Get a unique filename by appending numbers if needed.

        Args:
            base_path: Base path with .pdf extension

        Returns:
            Unique path that doesn't exist
        """
        if not base_path.exists():
            return base_path

        stem = base_path.stem
        suffix = base_path.suffix
        parent = base_path.parent

        counter = 1
        while True:
            new_path = parent / f"{stem} ({counter}){suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    def extract(
        self,
        page_title: Optional[str],
        first_screenshot: Optional[bytes] = None,
        prompt_on_failure: bool = True,
    ) -> str:
        """Extract company name using fallback chain.

        1. Parse page title
        2. OCR first slide
        3. Prompt user (if enabled)

        Args:
            page_title: DocSend page title
            first_screenshot: First page screenshot for OCR
            prompt_on_failure: Whether to prompt user if auto-detection fails

        Returns:
            Sanitized company name
        """
        # Try title parsing first
        name = self._from_title(page_title) if page_title else None
        if name:
            return self._sanitize_filename(name)

        # Try OCR fallback
        if first_screenshot:
            name = self._from_ocr(first_screenshot)
            if name:
                return self._sanitize_filename(name)

        # Prompt user as last resort
        if prompt_on_failure:
            name = self._prompt_user()
            return self._sanitize_filename(name)

        # Default fallback
        return "DocSend Document"

    def get_output_path(
        self,
        name: str,
        output_dir: str = "converted PDFs",
    ) -> Path:
        """Get the full output path for the PDF.

        Args:
            name: Company/document name
            output_dir: Output directory

        Returns:
            Full path for PDF file (unique, won't overwrite existing)
        """
        sanitized_name = self._sanitize_filename(name)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        base_path = output_path / f"{sanitized_name}.pdf"
        return self._get_unique_filename(base_path)
