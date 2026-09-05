#!/usr/bin/env python3
"""Design Engine — QA: a layout AND design gate.

Checks the REAL rendered layout of an HTML asset and the design health of its
slides. Fails on things that break a deck; warns on things that cheapen it.

Exit codes:
    0 = PASS (no failures; warnings may still be printed)
    1 = FAIL (geometry overflow, a broken/missing image, or an empty slide)
    2 = usage / file-not-found / render error

Checks
------
OVERFLOW  (fail)   a non-absolute element escapes its section/container bounds.
                   Uses boundingClientRect, NOT scrollHeight (which false-
                   positives on Montserrat display headings).

CLIP      (warn)   a text box may clip its glyphs (blink the false-positive on
                   display heading line boxes; verify with the box).

IMG-MISSING (fail) an <img> failed to load (naturalWidth === 0 / 404). Slides
                   render blank and nobody notices until delivery.
                   Fix: check images/* path and run scripts/image.py.

EMPTY-SLIDE (fail) a section has almost no content and no loaded image: a
                   dropped/forgotten slide. Intentional sparse "anchor" slides
                   (one big number, a bold statement) are excluded via the
                   big-text check.

NO-ALT     (warn)  an <img> is missing the alt attribute (a11y rule from
                   docs/formatting-standards.md). Decorative alt="" is fine;
                   only total absence is flagged.

SCRIM-RISK (warn)  white/near-white text sits over a plain full-bleed photo
                   with no treatment or overlay. Contrast is not guaranteed.
                   Fix: add a scrim or a brand tint / duotone overlay.

Usage:
    source venv/bin/activate
    python3 scripts/qa.py my-deck.html              # 0 = clean
    python3 scripts/qa.py my-deck.html --strict     # warnings also fail
    python3 scripts/qa.py my-deck.html --dump-text

Docs: docs/qa.md
"""
import argparse
import asyncio
import http.server
import os
import socketserver
import sys
import threading

FAIL_CHECKS = ("OVERFLOW", "IMG-MISSING", "EMPTY-SLIDE")
WARN_CHECKS = ("CLIP", "NO-ALT", "SCRIM-RISK")

QA_JS = r"""
() => {
  const result = { containers: [], checks: [], text: document.body.innerText };
  const push = (level, kind, {c=null, el=null, src=null, detail=''}={}) =>
    result.checks.push({level, kind, c, el, src, text: String((el&&el.textContent)||src||detail||'').trim().slice(0,46)});

  function luminanceOf(color){
    const m = /rgba?\(([\d.]+)[, ]+([\d.]+)[, ]+([\d.]+)/.exec(color || '');
    if(!m) return 0;
    return 0.2126*(+m[1]) + 0.7152*(+m[2]) + 0.0722*(+m[3]);
  }
  function area(r){ return (r.width>0 && r.height>0) ? r.width*r.height : 0; }

  // ---- containers: sections, else the largest fixed-size box ----
  const sections = document.querySelectorAll('section');
  let containers = Array.from(sections);
  if(!containers.length){
    document.querySelectorAll('div').forEach(d=>{
      const r=d.getBoundingClientRect();
      const st=getComputedStyle(d);
      // decorative/overlay layers are not canvases — exclude them
      if(r.width>300 && r.height>300 && st.position!=='absolute' && st.position!=='fixed') containers.push(d);
    });
    if(!containers.length) containers.push(document.body);
  }

  containers.forEach((c, idx) => {
    const cr = c.getBoundingClientRect();
    result.containers.push({i: idx+1, w: Math.round(cr.width), h: Math.round(cr.height)});

    // ---- geometry: overflow (fail) + clip (warn) ----
    c.querySelectorAll('h1,h2,h3,p,span,div,li,td,th').forEach(el => {
      const style = getComputedStyle(el);
      if(style.position === 'absolute') return;            // ghost decorations bleed by design
      const r = el.getBoundingClientRect();
      if(r.width===0 || r.height===0) return;
      const oR = r.right > cr.right + 1;
      const oB = r.bottom > cr.bottom + 1;
      const oL = r.left < cr.left - 1;
      if(oR || oB || oL) push('fail','OVERFLOW',{c:idx+1, el, detail:
        `right+${Math.round(r.right-cr.right)} bottom+${Math.round(r.bottom-cr.bottom)}`});
      // clip: ignore display headings (line-box artifact); only real glyph risk
      if(el.scrollHeight > el.clientHeight + 4 && el.clientHeight > 0 && !['h1','h2'].includes(el.tagName))
        push('warn','CLIP',{c:idx+1, el});
    });

    // ---- images: missing (fail) + alt (warn) + scrim risk (warn) ----
    const imgs = Array.from(c.querySelectorAll('img'));
    const loaded = [];
    imgs.forEach(img => {
      const ok = img.complete && img.naturalWidth > 0;
      if(!ok){ push('fail','IMG-MISSING',{c:idx+1, el:img, src:img.getAttribute('src')}); }
      else loaded.push({el: img, r: img.getBoundingClientRect()});
      if(!img.hasAttribute('alt')) push('warn','NO-ALT',{c:idx+1, el:img, src:img.getAttribute('src')});
    });

    // ---- empty slide: no content, no loaded image, no big text block ----
    const textLen = (c.innerText || '').trim().length;
    let bigText = false;
    Array.from(c.querySelectorAll('*')).forEach(el => {
      const t=(el.textContent||'').trim();
      if(t.length < 2) return;
      const fs = parseFloat(getComputedStyle(el).fontSize || '0');
      if(fs < 20) return;
      const r = el.getBoundingClientRect();
      if(area(r) > cr.width*cr.height*0.05) bigText = true;
    });
    if(textLen < 12 && imgs.length === 0 && !bigText)
      push('fail','EMPTY-SLIDE',{c:idx+1, detail:`${textLen} chars`});

    // ---- scrim risk: white text over a PLAIN full-bleed photo ----
    loaded.forEach(im => {
      const ir = im.r;
      if(area(ir) < (cr.width*cr.height||1) * 0.5) return;   // not full-bleed
      if(getComputedStyle(im.el).filter !== 'none') return;   // treated (duotone etc.)
      // overlay covering the image (scrim, tint, blend) — any sibling/descendant covering it
      let covered = false;
      c.querySelectorAll('div,span').forEach(o => {
        if(o === im.el || o.contains(im.el)) return;          // ancestors/containers are not overlays
        const or = o.getBoundingClientRect();
        const inter = Math.max(0, Math.min(or.right, ir.right)-Math.max(or.left, ir.left))
                    * Math.max(0, Math.min(or.bottom, ir.bottom)-Math.max(or.top, ir.top));
        if(inter >= ir.width*ir.height*0.25) covered = true;
      });
      if(covered) return;
      c.querySelectorAll('h1,h2,h3,p,span').forEach(t => {
        const tr = t.getBoundingClientRect();
        if(!area(tr)) return;
        const inter = Math.max(0, Math.min(tr.right, ir.right)-Math.max(tr.left, ir.left))
                    * Math.max(0, Math.min(tr.bottom, ir.bottom)-Math.max(tr.top, ir.top));
        if(inter < tr.width*tr.height*0.2) return;
        if(luminanceOf(getComputedStyle(t).color) >= 200)
          push('warn','SCRIM-RISK',{c:idx+1, el:t});
      });
    });
  });

  return result;
}
"""


def find_free_port():
    with socketserver.TCPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler) as s:
        return s.server_address[1]


async def run(html_file, dump_text, strict):
    from pyppeteer import launch
    if not os.path.exists(html_file):
        print(f"File not found: {html_file}")
        sys.exit(2)

    port = find_free_port()

    # Serve from the common parent of cwd and the asset's dir, so repo-relative
    # paths (../../images/...) AND standalone /tmp fixtures both resolve.
    abs_path = os.path.abspath(html_file)
    docroot = os.path.commonpath([os.getcwd(), os.path.dirname(abs_path)])
    url_path = os.path.relpath(abs_path, docroot)
    cwd = os.getcwd()
    os.chdir(docroot)

    httpd = socketserver.TCPServer(("127.0.0.1", port), http.server.SimpleHTTPRequestHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    browser = await launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    page = await browser.newPage()
    await page.setViewport({"width": 1920, "height": 1080})
    try:
        await page.goto(f"http://127.0.0.1:{port}/{url_path}", waitUntil="networkidle0", timeout=90000)
    finally:
        os.chdir(cwd)
    await asyncio.sleep(4)
    res = await page.evaluate(QA_JS)
    await browser.close()
    httpd.shutdown()

    if dump_text:
        print(res["text"])

    for con in res["containers"]:
        print(f"container {con['i']}: {con['w']} x {con['h']}px")

    checks = res["checks"]
    for ch in checks:
        mark = "FAIL" if ch["level"] == "fail" else "WARN"
        print(f"  {mark} [{ch['kind']}] slide {ch['c']} {ch['text']}")

    fails = [c for c in checks if c["level"] == "fail"]
    warns = [c for c in checks if c["level"] == "warn"]

    kf = {k: sum(1 for c in fails if c["kind"] == k) for k in FAIL_CHECKS}
    kw = {k: sum(1 for c in warns if c["kind"] == k) for k in WARN_CHECKS}
    summary = " ".join(f"{k}={kf[k]}" for k in FAIL_CHECKS if kf.get(k))
    summary_w = " ".join(f"{k}={kw[k]}" for k in WARN_CHECKS if kw.get(k))
    print(f"fails: {summary or '0'} | warns: {summary_w or '0'}")

    ok = not fails
    if ok and not (strict and warns):
        print("RESULT: PASS")
        return 0
    if ok:
        print("RESULT: PASS (with warnings)" + (" — --strict treats warnings as failures" if warns else ""))
        return 1 if strict else 0
    print("RESULT: FAIL — fix the fail-level issues")
    return 1


def main():
    p = argparse.ArgumentParser(description="Design Engine QA — layout and design gate")
    p.add_argument("file", help="path to HTML asset")
    p.add_argument("--strict", action="store_true", help="treat warnings as failures too")
    p.add_argument("--dump-text", action="store_true", help="print rendered DOM innerText")
    args = p.parse_args()
    sys.exit(asyncio.get_event_loop().run_until_complete(run(args.file, args.dump_text, args.strict)))


if __name__ == "__main__":
    main()