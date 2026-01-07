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
from rich.prompt import Confirm, Prompt

from topdf import __version__
from topdf.exceptions import InvalidURLError, OCRError, SummaryError, TopdfError

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
@click.argument("url", required=False)
@click.option(
    "--name", "-n",
    default=None,
    help="Output filename for the PDF (required for conversion)"
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
@click.option(
    "--check-key",
    is_flag=True,
    help="Show configured Perplexity API key status"
)
@click.option(
    "--reset-key",
    is_flag=True,
    help="Clear saved Perplexity API key"
)
@click.version_option(version=__version__, prog_name="topdf")
def topdf(
    url: Optional[str],
    name: Optional[str],
    email: Optional[str],
    passcode: Optional[str],
    output: str,
    verbose: bool,
    debug: bool,
    check_key: bool,
    reset_key: bool,
) -> None:
    """Convert a DocSend document to PDF.

    Downloads all pages from a DocSend link and saves them as a PDF file.
    Optionally generates an AI-powered structured summary using Perplexity.

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

      # Check API key status:
      topdf --check-key

      # Reset saved API key:
      topdf --reset-key
    """
    # Handle --check-key flag
    if check_key:
        _handle_check_key()
        return

    # Handle --reset-key flag
    if reset_key:
        _handle_reset_key()
        return

    # URL and name required for conversion
    if not url:
        console.print("[red]Error: URL is required for conversion[/red]")
        console.print("Usage: topdf URL --name 'Filename'")
        sys.exit(1)

    if not name:
        name = Prompt.ask("Enter filename for the PDF")
        if not name:
            console.print("[red]Error: Filename is required[/red]")
            sys.exit(1)

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

        # Offer AI summary
        _offer_summary(result, verbose)

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


def _handle_check_key() -> None:
    """Handle --check-key flag: display API key status."""
    from topdf import config

    if config.has_api_key():
        masked = config.get_masked_key()
        source = config.get_key_source()
        source_label = "config file" if source == "config" else "environment variable"
        console.print(f"[green]Perplexity API key configured[/green] (from {source_label})")
        console.print(f"  Key: {masked}")
    else:
        console.print("[yellow]No Perplexity API key configured[/yellow]")
        console.print("  Set via: PERPLEXITY_API_KEY environment variable")
        console.print("  Or run a conversion and save when prompted")


def _handle_reset_key() -> None:
    """Handle --reset-key flag: clear saved API key."""
    from topdf import config

    if not config.has_api_key():
        console.print("[yellow]No API key to reset[/yellow]")
        return

    if Confirm.ask("Clear saved Perplexity API key?", default=False):
        config.clear_api_key()
        console.print("[green]API key cleared[/green]")
    else:
        console.print("[dim]Cancelled[/dim]")


def _offer_summary(result, verbose: bool) -> None:
    """Offer to generate AI summary after PDF conversion.

    Args:
        result: ConversionResult from conversion
        verbose: Whether to show verbose output
    """
    console.print()

    # Ask if user wants summary
    if not Confirm.ask("Generate AI summary?", default=False):
        return

    # Import summarization modules
    from topdf import config, summarizer

    # Get or prompt for API key
    api_key = config.get_api_key()

    if not api_key:
        console.print()
        console.print("[dim]Perplexity API key required for summarization[/dim]")
        console.print("[dim]Get your key at: https://www.perplexity.ai/settings/api[/dim]")
        console.print()

        api_key = Prompt.ask("Enter your Perplexity API key")

        if not api_key:
            console.print("[yellow]No API key provided, skipping summary[/yellow]")
            return

        # Offer to save
        if Confirm.ask("Save key for future use?", default=True):
            config.save_api_key(api_key)
            console.print(f"[dim]Key saved to {config.CONFIG_FILE}[/dim]")

    # Generate summary
    console.print()
    console.print("[cyan]Analyzing deck...[/cyan]")

    try:
        summary = summarizer.summarize(api_key, result.screenshots)
        md_path = summarizer.write_summary(summary, result.pdf_path)

        console.print()
        console.print(f"[green bold]Summary saved to:[/green bold]")
        console.print(f"  [cyan]{md_path}[/cyan]")

        # Show preview
        console.print()
        console.print(f"[bold]{summary.company.company_name}[/bold]")
        console.print(f"[dim]{summary.company.description}[/dim]")
        console.print(f"[dim]Sector: {summary.company.primary_sector}[/dim]")
        if summary.funded_peers:
            console.print(f"[dim]Found {len(summary.funded_peers)} funded peers[/dim]")

    except OCRError as e:
        console.print(f"[yellow]Warning: {e.message}[/yellow]")
        console.print("[dim]PDF was saved successfully[/dim]")
    except SummaryError as e:
        console.print(f"[yellow]Warning: {e.message}[/yellow]")
        if verbose and e.cause:
            console.print(f"[dim]Cause: {e.cause}[/dim]")
        console.print("[dim]PDF was saved successfully[/dim]")


def main() -> None:
    """Main entry point for the CLI."""
    topdf()


if __name__ == "__main__":
    main()
