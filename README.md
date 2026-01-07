# topdf

A command-line tool that converts DocSend document links to local PDF files.

## Features

- **Local Processing** - All conversion happens on your machine, no data sent to third parties
- **Authentication Support** - Handles email-gated and password-protected documents
- **Full Document Capture** - Downloads all pages with exact visual fidelity
- **Simple CLI** - Easy to use command-line interface
- **AI Summarization** - Optional structured analysis with company overview, sector tags, and funded peer discovery via Perplexity

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

# Optional: Install AI summarization support
pip install -e ".[summarize]"
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

### AI Summarization

After PDF conversion, you'll be prompted to generate an AI summary. This requires a Perplexity API key.

```bash
# Check if API key is configured
topdf --check-key

# Clear saved API key
topdf --reset-key
```

**Get your API key at:** https://www.perplexity.ai/settings/api

The summary includes:
- Company description and sector classification
- Customer traction indicators
- Up to 10 recently funded peer companies (global, last 24 months)

Output is saved as a markdown file alongside the PDF.

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
  --check-key          Show configured Perplexity API key status
  --reset-key          Clear saved Perplexity API key
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
6. (Optional) OCR extracts text → Perplexity analyzes deck and finds funded peers → Markdown summary saved

## Requirements

- `playwright` - Browser automation
- `Pillow` - Image processing
- `img2pdf` - PDF generation
- `click` - CLI framework
- `rich` - Progress display
- `pytesseract` - OCR (optional, for name detection)
- `openai` - Perplexity API client (optional, for AI summarization)

## License

MIT License

## Version

Current version: **1.0.2**

---

## How to Use

Step-by-step guide for cloning this repository and running the tool:

### 1. Clone the Repository

```bash
git clone https://github.com/RTinkslinger/pdf-bot-v1.git
cd pdf-bot-v1
```

### 2. Create a Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install the Package

```bash
pip install -e .
```

### 4. Install Playwright Browser

```bash
playwright install chromium
```

### 5. (Optional) Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### 6. Run the Tool

```bash
topdf https://docsend.com/view/YOUR_DOCUMENT_ID --name "Your Filename"
```

### Quick Start Example

```bash
# Clone and setup (one-time)
git clone https://github.com/RTinkslinger/pdf-bot-v1.git
cd pdf-bot-v1
python3 -m venv venv
source venv/bin/activate
pip install -e .
playwright install chromium

# Convert a document
topdf https://docsend.com/view/abc123 -n "My Document" -e your@email.com
```

### Troubleshooting

**"command not found: topdf"**
- Make sure you activated the virtual environment: `source venv/bin/activate`

**"playwright not found"**
- Run: `playwright install chromium`

**Authentication errors**
- Some documents require email (`-e`) or passcode (`-p`)
- Use `--debug` flag to see the browser and troubleshoot
