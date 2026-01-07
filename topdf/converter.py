"""
Conversion Orchestrator
=======================
Main orchestrator that coordinates the DocSend to PDF conversion workflow.

This module ties together:
- DocSendScraper: Browser automation and screenshot capture
- NameExtractor: Document name extraction
- PDFBuilder: Screenshot to PDF conversion
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from topdf.name_extractor import NameExtractor
from topdf.pdf_builder import PDFBuilder
from topdf.scraper import DocSendScraper


@dataclass
class ConversionResult:
    """Result of a successful document conversion.

    Attributes:
        pdf_path: Path to the generated PDF file
        company_name: Extracted or provided document name
        page_count: Number of pages in the document
        screenshots: Raw screenshot bytes (for optional summarization)
    """
    pdf_path: Path
    company_name: str
    page_count: int
    screenshots: list[bytes]


class Converter:
    """Orchestrates the DocSend to PDF conversion workflow.

    Coordinates the scraper, name extractor, and PDF builder to convert
    a DocSend document into a local PDF file.

    Usage:
        converter = Converter(output_dir="pdfs")
        result = await converter.convert(url, email="user@example.com")
        print(f"Saved to {result.pdf_path}")
    """

    def __init__(
        self,
        output_dir: str = "converted PDFs",
        headless: bool = True,
    ):
        """Initialize the converter.

        Args:
            output_dir: Directory to save converted PDFs
            headless: Run browser in headless mode (False for debugging)
        """
        self.output_dir = output_dir
        self.headless = headless
        self.console = Console()

    async def convert(
        self,
        url: str,
        email: Optional[str] = None,
        passcode: Optional[str] = None,
        output_name: Optional[str] = None,
        verbose: bool = False,
    ) -> ConversionResult:
        """Convert a DocSend document to PDF.

        Workflow:
        1. Scrape document (capture all page screenshots)
        2. Extract document name (from user input or page title)
        3. Build PDF from screenshots
        4. Save PDF to output directory

        Args:
            url: DocSend document URL
            email: Email for email-protected documents
            passcode: Passcode for password-protected documents
            output_name: Override the output filename
            verbose: Print detailed progress output

        Returns:
            ConversionResult with path, name, and page count

        Raises:
            TopdfError: If any step of conversion fails
        """
        # Initialize components
        scraper = DocSendScraper(headless=self.headless, verbose=verbose)
        pdf_builder = PDFBuilder(optimize=True)
        name_extractor = NameExtractor(use_ocr=True)

        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        ) as progress:
            main_task = progress.add_task(
                "[cyan]Converting document...",
                total=100,
            )

            # Step 1: Scrape document (60% of work)
            progress.update(main_task, description="[cyan]Loading document...")

            def update_scrape_progress(current: int, total: int) -> None:
                """Callback to update progress during scraping."""
                pct = int((current / total) * 60)
                progress.update(
                    main_task,
                    completed=pct,
                    description=f"[cyan]Capturing page {current}/{total}...",
                )

            scrape_result = await scraper.scrape(
                url=url,
                email=email,
                passcode=passcode,
                progress_callback=update_scrape_progress,
            )
            progress.update(main_task, completed=60)

            # Step 2: Determine document name (5% of work)
            progress.update(main_task, description="[cyan]Extracting document name...")

            if output_name:
                # Use user-provided name
                company_name = output_name
            else:
                # Extract from page title or OCR
                company_name = name_extractor.extract(
                    page_title=scrape_result.page_title,
                    first_screenshot=scrape_result.screenshots[0] if scrape_result.screenshots else None,
                    prompt_on_failure=True,
                )
            progress.update(main_task, completed=65)

            # Step 3: Build PDF (30% of work)
            progress.update(main_task, description="[cyan]Building PDF...")

            pdf_bytes = pdf_builder.build(scrape_result.screenshots)
            progress.update(main_task, completed=95)

            # Step 4: Save PDF (5% of work)
            progress.update(main_task, description="[cyan]Saving PDF...")

            output_path = name_extractor.get_output_path(
                name=company_name,
                output_dir=self.output_dir,
            )
            output_path.write_bytes(pdf_bytes)
            progress.update(main_task, completed=100)

        return ConversionResult(
            pdf_path=output_path,
            company_name=company_name,
            page_count=scrape_result.page_count,
            screenshots=scrape_result.screenshots,
        )
