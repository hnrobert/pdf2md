# pdf2dotmd

A Python CLI tool that converts PDF files to Markdown format with intelligent layout analysis.

## Features

- **Layout-aware text extraction** — reconstructs logical reading order from PDF spatial data
- **Multi-column detection** — handles two-column and multi-column layouts
- **Table extraction** — converts PDF tables to Markdown pipe tables
- **Heading inference** — detects headings from font size hierarchy
- **Header/footer filtering** — automatically removes repeated page headers and footers
- **Image extraction** — extracts embedded images to an `assets/` directory
- **Ignore images mode** — `--ignore-images` flag for text-only output
- **Page range selection** — convert specific pages only
- **Batch conversion** — process multiple PDF files with wildcards

## Installation

```bash
pip install pdf2dotmd
```

## Usage

```bash
# Output to stdout
pdf2dotmd input.pdf

# Output to file
pdf2dotmd input.pdf -o output.md

# Skip images, output single Markdown file
pdf2dotmd input.pdf --ignore-images

# Batch conversion
pdf2dotmd *.pdf -o output_dir/

# Convert only specific pages
pdf2dotmd input.pdf -p 1-3
pdf2dotmd input.pdf -p 1-5,8,10-12

# Verbose logging
pdf2dotmd input.pdf -v
```

## How It Works

1. **Character extraction** — uses [pdfplumber](https://github.com/jsvine/pdfplumber) to extract individual characters with position data
2. **Line grouping** — clusters characters into text lines by y-coordinate proximity
3. **Block formation** — groups lines into paragraphs based on horizontal alignment and vertical spacing
4. **Column detection** — identifies multi-column layouts by analyzing horizontal text density gaps
5. **Reading order** — sorts blocks top-to-bottom, left-to-right, handling spanning titles
6. **Header/footer removal** — detects repeated elements across pages
7. **Heading inference** — maps font sizes to heading levels (H1-H6)

## Limitations

- **Scanned PDFs** — OCR is not supported; scanned/image-only PDFs will produce empty output
- **Encrypted PDFs** — password-protected PDFs are not supported
- **Complex layouts** — highly irregular layouts may not parse perfectly

## License

MIT
