"""
Command Line Interface for topdf
================================
Entry point for the topdf CLI tool.

Usage:
    topdf URL --name "Filename" [options]

Run `topdf --help` for full usage information.
"""

import asyncio
import re
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from topdf import __version__
from topdf.exceptions import InvalidURLError, TopdfError

console = Console()

# DocSend URL validation pattern
DOCSEND_URL_PATTERN = re.compile(
    r"^https?://(www\.)?docsend\.com/view/[\w-]+/?$"
)


def validate_url(url: str) -> str:
    """Validate that the URL is a valid DocSend link.

    Args:
        url: URL to validate

    Returns:
        The validated URL

    Raises:
        InvalidURLError: If URL is not a valid DocSend link
    """
    if not DOCSEND_URL_PATTERN.match(url):
        raise InvalidURLError(url)
    return url


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("url")
@click.option(
    "--name", "-n",
    required=True,
    prompt="Enter filename for the PDF",
    help="Output filename for the PDF (required)"
)
@click.option(
    "--email", "-e",
    default=None,
    help="Email address for protected documents"
)
@click.option(
    "--passcode", "-p",
    default=None,
    help="Passcode for password-protected documents"
)
@click.option(
    "--output", "-o",
    default="converted PDFs",
    show_default=True,
    help="Output directory for saved PDFs"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed progress output"
)
@click.option(
    "--debug",
    is_flag=True,
    help="Show browser window for debugging"
)
@click.version_option(version=__version__, prog_name="topdf")
def topdf(
    url: str,
    name: str,
    email: Optional[str],
    passcode: Optional[str],
    output: str,
    verbose: bool,
    debug: bool,
) -> None:
    """Convert a DocSend document to PDF.

    Downloads all pages from a DocSend link and saves them as a PDF file.

    \b
    ARGUMENTS:
      URL    DocSend document URL (e.g., https://docsend.com/view/abc123)

    \b
    EXAMPLES:
      # Basic usage (will prompt for filename):
      topdf https://docsend.com/view/abc123

      # With filename specified:
      topdf https://docsend.com/view/abc123 --name "Company Pitch Deck"

      # Email-protected document:
      topdf https://docsend.com/view/abc123 -n "Deck" -e user@example.com

      # Password-protected document:
      topdf https://docsend.com/view/abc123 -n "Deck" -e user@example.com -p secret

      # Custom output directory:
      topdf https://docsend.com/view/abc123 -n "Deck" -o ~/Desktop
    """
    try:
        # Validate URL format
        validate_url(url)

        # Show configuration in verbose mode
        if verbose:
            console.print(f"[dim]URL: {url}[/dim]")
            console.print(f"[dim]Filename: {name}[/dim]")
            if email:
                console.print(f"[dim]Email: {email}[/dim]")
            console.print(f"[dim]Output directory: {output}[/dim]")

        # Import converter here to speed up --help response
        from topdf.converter import Converter

        # Ensure output directory exists
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)

        # Run the conversion
        converter = Converter(output_dir=output, headless=not debug)
        result = asyncio.run(
            converter.convert(
                url=url,
                email=email,
                passcode=passcode,
                output_name=name,
                verbose=verbose or debug,
            )
        )

        # Display success message
        console.print()
        console.print(f"[green bold]Success![/green bold] PDF saved to:")
        console.print(f"  [cyan]{result.pdf_path}[/cyan]")
        console.print(f"  [dim]{result.page_count} pages[/dim]")

    except TopdfError as e:
        console.print(f"\n[red bold]{e}[/red bold]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red bold]Unexpected error: {e}[/red bold]")
        if verbose:
            console.print_exception()
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    topdf()


if __name__ == "__main__":
    main()
