# topdf

A command-line tool that converts DocSend document links to local PDF files.

## Features

- **Local Processing** - All conversion happens on your machine, no data sent to third parties
- **Authentication Support** - Handles email-gated and password-protected documents
- **Full Document Capture** - Downloads all pages with exact visual fidelity
- **Simple CLI** - Easy to use command-line interface

## Installation

### Prerequisites

- Python 3.9 or higher
- Tesseract OCR (optional, for automatic name detection)

### Setup

```bash
# Clone the repository
git clone https://github.com/RTinkslinger/pdf-bot-v1.git
cd pdf-bot-v1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install Playwright browser
playwright install chromium

# Optional: Install Tesseract for OCR (macOS)
brew install tesseract
```

## Usage

### Basic Usage

```bash
topdf https://docsend.com/view/abc123 --name "Document Name"
```

### With Email Authentication

```bash
topdf https://docsend.com/view/abc123 -n "Pitch Deck" -e user@example.com
```

### With Email + Passcode

```bash
topdf https://docsend.com/view/abc123 -n "Pitch Deck" -e user@example.com -p secret123
```

### Custom Output Directory

```bash
topdf https://docsend.com/view/abc123 -n "Pitch Deck" -o ~/Desktop
```

### Debug Mode (Show Browser)

```bash
topdf https://docsend.com/view/abc123 -n "Pitch Deck" --debug
```

## Command Reference

```
Usage: topdf [OPTIONS] URL

Options:
  -n, --name TEXT      Output filename for the PDF (required)
  -e, --email TEXT     Email address for protected documents
  -p, --passcode TEXT  Passcode for password-protected documents
  -o, --output TEXT    Output directory [default: converted PDFs]
  -v, --verbose        Show detailed progress output
  --debug              Show browser window for debugging
  --version            Show the version and exit
  -h, --help           Show this message and exit
```

## Output

PDFs are saved to the `converted PDFs` folder by default (or your specified output directory).

## How It Works

1. Opens DocSend URL in a headless browser (Chromium)
2. Handles authentication if required (email/passcode)
3. Navigates through all pages and captures screenshots
4. Combines screenshots into a single PDF file
5. Saves to your specified location

## Requirements

- `playwright` - Browser automation
- `Pillow` - Image processing
- `img2pdf` - PDF generation
- `click` - CLI framework
- `rich` - Progress display
- `pytesseract` - OCR (optional)

## License

MIT License

## Version

Current version: **1.0.0**
