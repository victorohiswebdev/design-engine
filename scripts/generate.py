#!/usr/bin/env python3
"""Design Engine — unified render CLI.

Renders any HTML template to PDF or PNG through headless Chromium (Pyppeteer).

Usage:
    source venv/bin/activate
    python3 scripts/generate.py deck my-deck.html          # → my-deck.pdf (1920x1080)
    python3 scripts/generate.py a4 my-doc.html             # → my-doc.pdf (A4)
    python3 scripts/generate.py flyer flyer.html --format png # → flyer.png (1080x1350)
    python3 scripts/generate.py carousel carousel.html --format png  # → carousel.png (1080x1080)

Args:
    <type>       deck | a4 | flyer | carousel
    <file>       path to the HTML template (relative to repo root or absolute)
    --format     pdf (default) or png
    --out PATH   override output path

Rendering notes (see docs/pdf-pipeline.md):
    - Force-loads every font weight then waits for document.fonts.ready.
    - Uses a local HTTP server (real origin, not file://) for Tailwind + fonts.
    - Loops ports so a stale server from a prior run doesn't block binding.
    - PNG output is a full-canvas screenshot (flyer/carousel).
"""
import argparse
import asyncio
import os
import socketserver
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Canvas per output type. 'deck' emits a per-slide PDF; 'flyer'/'carousel'
# screenshot a square single-canvas image; 'a4' emits a formatted PDF.
CANVAS = {
    'deck':            {'width': 1920, 'height': 1080, 'pdf': '1920px', 'pdf_h': '1080px'},
    'a4':              {'width': 794,  'height': 1123, 'pdf': '210mm',  'pdf_h': '297mm'},
    'flyer':           {'width': 1080, 'height': 1350, 'pdf': '1080px', 'pdf_h': '1350px'},
    'carousel':        {'width': 1080, 'height': 1080, 'pdf': '1080px', 'pdf_h': '1080px'},
    'social':          {'width': 1080, 'height': 1080, 'pdf': '1080px', 'pdf_h': '1080px'},
    'social-portrait': {'width': 1080, 'height': 1350, 'pdf': '1080px', 'pdf_h': '1350px'},
    'story':           {'width': 1080, 'height': 1920, 'pdf': '1080px', 'pdf_h': '1920px'},
}

FONT_WEIGHTS = ["400", "500", "600", "700", "800", "900"]


def find_html(path):
    """Resolve an HTML path relative to the repo root if not absolute."""
    if os.path.isabs(path):
        return path
    for base in (ROOT, os.path.join(ROOT, 'templates')):
        cand = os.path.join(base, path)
        if os.path.exists(cand):
            return cand
    # Fall back to cwd-relative as-is so failure surfaces clearly.
    return path


def default_out(file, fmt):
    return file.rsplit('.html', 1)[0] + f'.{fmt}'


async def _force_fonts(page, timeout=8):
    """Force-load every font weight, then wait for ready (guards render)."""
    try:
        await page.evaluate("""async () => {
            await Promise.all(%s.map(w => document.fonts.load(w + ' 16px Montserrat')));
            await document.fonts.ready;
        }""" % (FONT_WEIGHTS,))
    except Exception:
        pass  # font loading is best-effort; a network hiccup shouldn't kill the render


def find_free_port():
    """Bind a free port and release it (loops past stale servers from prior runs)."""
    with socketserver.TCPServer(("127.0.0.1", 0), socketserver.BaseRequestHandler) as s:
        return s.server_address[1]


async def generate(type_, file, fmt, out):
    from pyppeteer import launch

    html = find_html(file)
    if not os.path.exists(html):
        print(f"File not found: {html}")
        sys.exit(2)

    canvas = CANVAS[type_]
    port = find_free_port()
    server = subprocess.Popen(
        ['python3', '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', ROOT])

    browser = None
    try:
        browser = await launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = await browser.newPage()
        await page.setViewport({'width': canvas['width'], 'height': canvas['height']})
        url = f"http://127.0.0.1:{port}/{os.path.relpath(html, ROOT)}"
        print(f"Loading {url} ...")
        await page.goto(url, waitUntil='networkidle0', timeout=90000)
        await asyncio.sleep(4)
        await _force_fonts(page)

        os.makedirs(os.path.dirname(os.path.abspath(out)) or '.', exist_ok=True)
        if fmt == 'pdf':
            await page.pdf({
                'path': out, 'printBackground': True,
                'width': canvas['pdf'], 'height': canvas['pdf_h'],
                'margin': {'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
            })
        else:
            await page.screenshot({'path': out, 'clip': {
                'x': 0, 'y': 0, 'width': canvas['width'], 'height': canvas['height']}})
        size = os.path.getsize(out)
        print(f"Done: {out} ({size:,} bytes)")
    finally:
        if browser:
            await browser.close()
        server.terminate()


def main():
    p = argparse.ArgumentParser(description="Design Engine render CLI")
    p.add_argument('type', choices=list(CANVAS.keys()), help='output type')
    p.add_argument('file', help='path to HTML template')
    p.add_argument('--format', choices=['pdf', 'png'], default='pdf', dest='fmt')
    p.add_argument('--out', default=None)
    args = p.parse_args()
    out = args.out or default_out(args.file, args.fmt)
    asyncio.get_event_loop().run_until_complete(generate(args.type, args.file, args.fmt, out))


if __name__ == '__main__':
    main()