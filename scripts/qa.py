#!/usr/bin/env python3
"""Design Engine — layout QA.

Checks the REAL rendered layout of an HTML asset: does any non-absolute element
escape its slide/container bounds (overflow), and does any text box clip its
glyphs? Uses boundingClientRect vs the container, NOT naive scrollHeight — the
naive check false-positives on Montserrat display headings whose font metrics
exceed the line box even when nothing is clipped.

Usage:
    source venv/bin/activate
    python3 scripts/qa.py my-deck.html          # exit 0 = clean, 1 = overflow
    python3 scripts/qa.py my-deck.html --dump-text

Containers are auto-detected: for a deck it's each <section>; otherwise it's the
largest fixed-size container (e.g. the 1080x1350 flyer/1080x1080 carousel box).

Docs: docs/qa.md
"""
import argparse
import asyncio
import http.server
import os
import socketserver
import sys
import threading


def find_free_port():
    with socketserver.TCPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler) as s:
        return s.server_address[1]


URL_JS = """
() => {
  const result = { containers: [], overflow: [], clipped: [], text: document.body.innerText };

  // Deck: check each <section>. Other types: check the largest fixed-size
  // non-body container (flyer/carousel box or the document root).
  const sections = document.querySelectorAll('section');
  let containers = Array.from(sections);
  if (!containers.length) {
    document.querySelectorAll('div').forEach(d => {
      const r = d.getBoundingClientRect();
      if (r.width > 300 && r.height > 300) containers.push(d);
    });
    if (!containers.length) containers.push(document.body);
  }

  containers.forEach((c, i) => {
    const cr = c.getBoundingClientRect();
    result.containers.push({i: i + 1, w: Math.round(cr.width), h: Math.round(cr.height)});
    c.querySelectorAll('h1,h2,h3,p,span,div,li,td,th').forEach(el => {
      const style = getComputedStyle(el);
      if (style.position === 'absolute') return;      // ghost decorations bleed by design
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return;
      const overflowRight = r.right > cr.right + 1;
      const overflowBottom = r.bottom > cr.bottom + 1;
      const overflowLeft = r.left < cr.left - 1;
      if (overflowRight || overflowBottom || overflowLeft) {
        result.overflow.push({c: i + 1, el: el.tagName, text: (el.textContent||'').trim().slice(0, 40),
          right: Math.round(r.right - cr.right), bottom: Math.round(r.bottom - cr.bottom)});
      }
      // Clip: real glyph clipping only on non-display text (display headings
      // report a benign line-box artifact — use leading-[1.25]+ if flagged).
      if (el.scrollHeight > el.clientHeight + 4 && el.clientHeight > 0 &&
          !['h1','h2'].includes(el.tagName)) {
        result.clipped.push({c: i + 1, el: el.tagName, text: (el.textContent||'').trim().slice(0, 40)});
      }
    });
  });
  return result;
}
"""


async def run(html_file, dump_text):
    from pyppeteer import launch

    if not os.path.exists(html_file):
        print(f"File not found: {html_file}")
        sys.exit(2)

    port = find_free_port()
    httpd = socketserver.TCPServer(("127.0.0.1", port), http.server.SimpleHTTPRequestHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    browser = await launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    page = await browser.newPage()
    await page.setViewport({"width": 1920, "height": 1080})
    await page.goto(f"http://127.0.0.1:{port}/{html_file}", waitUntil="networkidle0", timeout=90000)
    await asyncio.sleep(4)
    res = await page.evaluate(URL_JS)
    await browser.close()
    httpd.shutdown()

    if dump_text:
        print(res["text"])

    for c in res["containers"]:
        print(f"container {c['i']}: {c['w']} x {c['h']}px")
    for o in res["overflow"]:
        print(f"OVERFLOW container {o['c']} {o['el']} '{o['text']}' right={o['right']} bottom={o['bottom']}")
    for l in res["clipped"]:
        print(f"CLIP container {l['c']} {l['el']} '{l['text']}' (if display heading, use leading-[1.25]+)")

    if res["overflow"]:
        print("RESULT: FAIL — elements escape their container bounds")
        return 1
    if res["clipped"]:
        print("RESULT: WARN — possible glyph clip (verify the box)")
        return 1
    print("RESULT: PASS — all elements within container bounds")
    return 0


def main():
    p = argparse.ArgumentParser(description="Design Engine layout QA — bounds + clip + text")
    p.add_argument("file", help="path to HTML asset")
    p.add_argument("--dump-text", action="store_true", help="print rendered DOM innerText")
    args = p.parse_args()
    sys.exit(asyncio.get_event_loop().run_until_complete(run(args.file, args.dump_text)))


if __name__ == "__main__":
    main()