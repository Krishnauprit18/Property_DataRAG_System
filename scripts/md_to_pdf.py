#!/usr/bin/env python3
"""
Convert a Markdown file to a simple PDF using ReportLab.
This is a lightweight converter: it renders headings and paragraphs, 
but does not support full Markdown features (tables/images).
"""
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
import markdown as md


def md_to_paragraphs(markdown_text: str):
    """Convert Markdown text to a list of Paragraph and Spacer elements."""
    # Convert Markdown to basic HTML
    html = md.markdown(markdown_text)

    # Split paragraphs by <p> and headings by <h1..h6>
    # For simplicity, we'll just wrap the entire HTML as a Paragraph.
    # ReportLab's Paragraph supports a small subset of HTML.
    styles = getSampleStyleSheet()
    body = []

    # Tweak base style
    normal = styles['Normal']
    normal.fontName = 'Helvetica'
    normal.fontSize = 10
    normal.leading = 14

    # Lightweight approach: split by block tags we care about
    import re
    blocks = re.split(r'(</?h[1-6]>|<p>|</p>)', html)

    buffer = ''
    current_style = normal

    def flush_buffer(style):
        txt = buffer.strip()
        if txt:
            body.append(Paragraph(txt, style))
            body.append(Spacer(1, 6))

    # Map heading tags to sizes
    heading_sizes = {
        'h1': 18,
        'h2': 14,
        'h3': 12,
        'h4': 11,
        'h5': 10,
        'h6': 10,
    }

    tag_stack = []

    i = 0
    while i < len(blocks):
        token = blocks[i]
        if token is None:
            i += 1
            continue
        token = token.strip()
        if token == '':
            i += 1
            continue

        if token.startswith('<h') and token.endswith('>') and not token.startswith('</'):
            # Opening heading
            flush_buffer(current_style)
            tag = token.strip('<>')
            tag_stack.append(tag)
            size = heading_sizes.get(tag, 12)
            style = styles['Heading2'] if tag in ('h1', 'h2') else styles['Heading3']
            style.fontName = 'Helvetica-Bold'
            style.fontSize = size
            style.leading = size + 4
            current_style = style
            buffer = ''
        elif token.startswith('</h') and token.endswith('>'):
            # Closing heading
            flush_buffer(current_style)
            if tag_stack:
                tag_stack.pop()
            current_style = normal
            buffer = ''
        elif token == '<p>':
            flush_buffer(current_style)
            current_style = normal
            buffer = ''
        elif token == '</p>':
            flush_buffer(current_style)
            buffer = ''
        else:
            buffer += token + ' '
        i += 1

    flush_buffer(current_style)
    return body


def convert(markdown_path: Path, pdf_path: Path):
    text = markdown_path.read_text(encoding='utf-8')
    story = md_to_paragraphs(text)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=markdown_path.stem,
        author='Property Data RAG System'
    )
    doc.build(story)


def main():
    if len(sys.argv) < 3:
        print('Usage: md_to_pdf.py <input.md> <output.pdf>')
        sys.exit(1)
    md_file = Path(sys.argv[1]).resolve()
    pdf_file = Path(sys.argv[2]).resolve()
    if not md_file.exists():
        print(f'Input file not found: {md_file}')
        sys.exit(2)
    pdf_file.parent.mkdir(parents=True, exist_ok=True)
    convert(md_file, pdf_file)
    print(f'✓ Generated PDF: {pdf_file}')


if __name__ == '__main__':
    main()
