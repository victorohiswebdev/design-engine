#!/usr/bin/env python3
"""Design Engine — Vision QA (Phase 4)

The subjective layer that geometry alone cannot catch: muddy gradients, off-brand
colors, washed-out contrast, blurry images, and crowded spacing.

Why this exists
--------------
`qa.py` is geometric — it proves nothing escapes, nothing clips, no image 404s.
Vision QA is perceptual — it proves the slide *looks right* when a human stares
at it. A deck can pass every geometry check and still look cheap: a beige muddy
gradient where a crisp panel should be, a random teal that is not the brand teal,
white text 1.2:1 on a pale photo, a hero image that is obviously low-res, a slide
with 12px gutters and no air. Those are the failures clients notice in the room,
and they are invisible to boundingRect math.

How it works
------------
1. Serves the HTML, renders with headless Chromium (same pipeline as generate.py),
   and screenshots each <section> at exactly 1920×1080 into /tmp.
2. Runs heuristic vision checks on every PNG with Pillow (no API needed):
   - BRAND_DRIFT : dominant colors stray far from the declared brand palette
   - LOW_CONTRAST : global luminance range / σ suggests washed-out, flat slides
   - MUDDY_GRADIENT : large desaturated midtone wash = stock-gradient mud
   - CROWDING / SPARSE : too little or too much whitespace
   - BLUR : Laplacian variance on the screenshot — blurry hero images
3. Optionally, with --vision and an API key, sends each slide to a vision LLM for
   a second pass against the 2026 formatting standards. Supports any vision
   provider via an OpenAI-compatible API or native Gemini/Anthropic. Keys:
   ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY / GOOGLE_API_KEY,
   or generic VISION_API_KEY + VISION_BASE_URL (for OpenRouter, Gemini
   OpenAI-compat, local models). Heuristics always run; LLM is additive.

Usage
-----
    source venv/bin/activate          # Pillow + pyppeteer already in venv
    pip install numpy                 # needed for blur/gradient checks (tiny dep)
    python3 scripts/vision_qa.py templates/deck/deck.html                # heuristics
    python3 scripts/vision_qa.py templates/deck/deck.html --brand livefree
    python3 scripts/vision_qa.py templates/deck/deck.html --vision        # + LLM (auto-detects provider from env)
    python3 scripts/vision_qa.py deck.html --vision --vision-provider gemini --vision-model gemini-2.0-flash
    python3 scripts/vision_qa.py deck.html --vision --vision-provider openai --vision-model gpt-4o
    GEMINI_API_KEY=... python3 scripts/vision_qa.py deck.html --vision         # Gemini via native API
    VISION_BASE_URL=https://openrouter.ai/api/v1 VISION_API_KEY=... python3 scripts/vision_qa.py deck.html --vision --vision-model google/gemini-2.0-flash
    python3 scripts/vision_qa.py templates/deck/deck.html --vision --strict
    python3 scripts/vision_qa.py templates/deck/deck.html --out report.json

Exit codes: 0 PASS, 1 FAIL, 2 error. FAIL = any heuristic FAIL or (with --strict)
any WARN. LLM opinions are always WARN-level — they never fail a build alone.

Design: deterministic heuristics are the gate; LLM is an advisor.
"""
import argparse
import asyncio
import base64
import http.server
import json
import math
import os
import socketserver
import sys
import threading
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BRANDS = {
    "neutral":  ["#1E2A38","#2E8B57","#F5F7FA","#FFFFFF","#000000"],
    "fyp":       ["#1E2A38","#2E8B57","#D4AF37","#DFF5E7","#F5F7FA","#FFFFFF","#000000"],
    "livefree":  ["#0b1120","#F97316","#0a6b8a","#00e5ff","#f8fafc","#ea580c","#FFFFFF","#000000"],
    "livefree-safari": ["#0b1120","#F97316","#0a6b8a","#00e5ff","#f8fafc","#ea580c","#FFFFFF","#000000"],
}
# alias
BRANDS["livefree"] = BRANDS["livefree"]
FONT_WEIGHTS = ["400","500","600","700","800","900"]

def hex_to_rgb(h):
    h=h.lstrip("#")
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def color_distance(c1, c2):
    return math.sqrt(sum((a-b)**2 for a,b in zip(c1,c2)))

def parse_brand(s):
    s=s.strip().lower()
    if s in BRANDS:
        return [hex_to_rgb(x) for x in BRANDS[s]]
    # custom: comma separated hexes
    if "," in s or s.startswith("#"):
        parts=[p.strip() for p in s.split(",")]
        return [hex_to_rgb(p) for p in parts if p]
    return [hex_to_rgb(x) for x in BRANDS["neutral"]]

# ---------- heuristics via Pillow ----------

def analyze_slide(png_path, brand_rgb, slide_idx):
    """Return list of {level, kind, detail} for one slide PNG."""
    from PIL import Image
    import numpy as np
    findings=[]

    im = Image.open(png_path).convert("RGB")
    w,h = im.size
    arr = np.array(im)  # h,w,3  uint8
    # downsample for palette speed
    small = im.resize((96,54), Image.BILINEAR)
    small_arr = np.array(small).reshape(-1,3)

    # ---- 1. brand drift ----
    # Skip photo-forward slides: photos naturally contain many off-palette hues.
    # Detect photo by high hue diversity + moderate saturation variance.
    tmp_hsv = im.resize((96,54), Image.BILINEAR).convert("HSV")
    hsv_arr = np.array(tmp_hsv)
    hue_unique = len(np.unique(hsv_arr[:,:,0]))
    sat_mean = float(hsv_arr[:,:,1].mean())
    is_photo_slide = hue_unique > 60 and sat_mean > 40  # heuristic: photos are hue-diverse
    if not is_photo_slide:
        # quantize to 6 colors, get dominant palette
        quantized = im.resize((192,108), Image.BILINEAR).quantize(colors=6, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette()[:18]  # 6*3
        from collections import Counter
        q_arr = np.array(quantized.resize((96,54), Image.NEAREST)).flatten()
        cnt = Counter(q_arr)
        total = sum(cnt.values())
        for idx, count in cnt.most_common(6):
            pct = count/total
            if pct < 0.08:
                continue
            r,g,b = palette[idx*3:idx*3+3]
            # skip near-white/black/gray and very desaturated UI grays
            if max(r,g,b) - min(r,g,b) < 18 and pct < 0.15:
                continue
            # need saturated color to be considered brand drift; grays are panel/bg
            mx, mn = max(r,g,b), min(r,g,b)
            sat_color = (mx - mn) / mx if mx else 0
            if sat_color < 0.30:
                continue
            dist = min(color_distance((r,g,b), br) for br in brand_rgb)
            if dist > 120:
                findings.append({"level":"warn","kind":"BRAND_DRIFT","detail":f"slide {slide_idx}: ~{pct:.0%} is rgb({r},{g},{b}) Δ{int(dist)} from palette — off-brand?"})
                break  # one per slide is enough noise

    # ---- 2. low contrast / washed out ----
    # luminance per Rec. 709
    lum = 0.2126*arr[:,:,0] + 0.7152*arr[:,:,1] + 0.0722*arr[:,:,2]
    l_min, l_max = float(lum.min()), float(lum.max())
    l_std = float(lum.std())
    l_range = l_max - l_min
    # a slide that is entirely within a narrow mid band is washed out
    if l_range < 95 and l_std < 28:
        findings.append({"level":"warn","kind":"LOW_CONTRAST","detail":f"slide {slide_idx}: luminance range {int(l_range)} σ {int(l_std)} — flat / washed out"})

    # ---- 3. muddy gradient — large low-saturation midtone wash ----
    # Convert RGB to HSV saturation quickly via max-min (avoid divide-by-zero warning)
    arr_f = arr.astype(np.float32)/255.0
    cmax = arr_f.max(axis=2)
    cmin = arr_f.min(axis=2)
    delta = cmax - cmin
    sat = np.divide(delta, cmax, out=np.zeros_like(cmax), where=cmax!=0)
    val = cmax
    muddy = ((sat < 0.12) & (val > 0.32) & (val < 0.88) & (lum > 55) & (lum < 225))
    muddy_ratio = float(muddy.mean())
    if muddy_ratio > 0.38 and not is_photo_slide:
        findings.append({"level":"warn","kind":"MUDDY_GRADIENT","detail":f"slide {slide_idx}: {muddy_ratio:.0%} desaturated mid — muddy gradient / beige wash"})

    # ---- 4. whitespace / crowding ----
    near_white = (lum > 242)
    white_ratio = float(near_white.mean())
    if not is_photo_slide:
        if white_ratio < 0.03:
            # very little air; but dark slides are intentional — check if overall dark
            dark_ratio = float((lum < 30).mean())
            if dark_ratio < 0.35:  # not a dark-mode slide
                findings.append({"level":"warn","kind":"CROWDING","detail":f"slide {slide_idx}: only {white_ratio:.0%} whitespace — dense / no air"})
        if white_ratio > 0.88:
            # also check text presence via edge density to avoid flagging intentional minimal slides
            # simple: if also low std, it's a blankish slide; but allow sparse if has large display text (exclude via std only)
            if l_std < 22:
                # check for big display numeral: if top N luminance variance suggests intentional hero number, skip
                if white_ratio < 0.96:
                    findings.append({"level":"warn","kind":"SPARSE","detail":f"slide {slide_idx}: {white_ratio:.0%} white, σ {int(l_std)} — reads blank"})

    # ---- 5. blur (Laplacian variance) on downsampled gray ----
    try:
        gray_small = np.array(Image.open(png_path).convert("L").resize((480,270), Image.BILINEAR), dtype=np.float32)
        # 3x3 Laplacian kernel
        lap = (
            -4*gray_small[1:-1,1:-1]
            + gray_small[:-2,1:-1] + gray_small[2:,1:-1]
            + gray_small[1:-1,:-2] + gray_small[1:-1,2:]
        )
        var = float(lap.var())
        if var < 18:
            findings.append({"level":"warn","kind":"BLUR","detail":f"slide {slide_idx}: Laplacian var {var:.1f} — soft / low-res image"})
    except Exception:
        pass

    return findings

VISION_PROMPT = """You are a senior presentation designer auditing ONE slide image against the 2026 Design Engine formatting standards.

Standards to check:
1. Title is a full-sentence conclusion (≤15 words), not a topic label.
2. Four-layer hierarchy — adjacent layers differ ≥1.5:1, body ≥24px.
3. WCAG contrast, CVD-safe, no decorative gold body text.
4. Brand palette coherence — LiveFree vivid orange/teal/cyan on near-black shows its free, FYP feels muted, Neutral the control.
5. Depth without clutter — soft shadows only, one depth move per deck, no heavy gradients, no glass blur that would drop in PDF.
6. Image treatment consistency and scrim coverage where text sits on photo.
7. Spacing: generous air, no crowding, no orphans, no clipping.

Look at the rendered slide image. Be concise and specific.

Return ONLY valid JSON with this shape:
{"score": 0-10, "issues": [{"severity":"warn|fail","kind":"SHORT_CODE","detail":"one sentence"}], "praise": "one sentence if score >=8 else empty"}
Severity fail only if the slide is objectively broken/ships wrong. Most issues are warn. If the slide is clean, return score 9-10 and empty issues.
"""

async def call_vision_llm(png_path, slide_idx, provider=None, model=None, api_key=None, base_url=None):
    """Provider-agnostic vision LLM call.

    Priority: explicit --vision-provider / env VISION_PROVIDER, else auto-detect
    from available keys (GEMINI_API_KEY/GOOGLE_API_KEY, ANTHROPIC_API_KEY,
    OPENAI_API_KEY, VISION_API_KEY).

    Supported providers:
      anthropic  — Anthropic Claude (ANTHROPIC_API_KEY)
      openai     — OpenAI and any OpenAI-compatible endpoint (OPENAI_API_KEY + optional OPENAI_BASE_URL / VISION_BASE_URL)
      gemini     — Google Gemini native API (GEMINI_API_KEY / GOOGLE_API_KEY)
      auto       — detect from env (default)

    Also honors generic VISION_API_KEY / VISION_BASE_URL / VISION_MODEL for
    OpenRouter, Ollama, local vLLM, etc. Returns list of findings or None if
    no key (graceful degrade).
    """
    b64 = base64.b64encode(Path(png_path).read_bytes()).decode()
    prompt = VISION_PROMPT + f"\nSlide index: {slide_idx}"

    # Resolve provider / model / key / base_url from explicit args > env > defaults
    env_provider = (provider or os.environ.get("VISION_PROVIDER") or os.environ.get("VISION_LLM_PROVIDER") or "auto").strip().lower()
    env_model = model or os.environ.get("VISION_MODEL") or os.environ.get("VISION_LLM_MODEL")
    env_api_key = api_key or os.environ.get("VISION_API_KEY")
    env_base_url = base_url or os.environ.get("VISION_BASE_URL") or os.environ.get("OPENAI_BASE_URL")

    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_GENAI_API_KEY")
    anth_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    # Normalize "auto" -> first available key
    if env_provider in ("auto", "", "detect"):
        if gemini_key and not anth_key and not openai_key:
            env_provider = "gemini"
        elif anth_key:
            env_provider = "anthropic"
        elif openai_key or env_api_key or env_base_url:
            env_provider = "openai"
        elif gemini_key:
            env_provider = "gemini"
        else:
            env_provider = "none"

    def _model_for(p, fallback):
        return env_model or fallback

    # --- Anthropic ---
    if env_provider == "anthropic":
        key = env_api_key or anth_key
        if not key:
            return None
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key, base_url=env_base_url or None)
            resp = client.messages.create(
                model=_model_for("anthropic", "claude-3-5-sonnet-latest"),
                max_tokens=600,
                messages=[{"role":"user","content":[
                    {"type":"text","text": prompt},
                    {"type":"image","source":{"type":"base64","media_type":"image/png","data": b64}}
                ]}]
            )
            text = "".join(c.text for c in resp.content if hasattr(c,"text"))
            return parse_llm_json(text, slide_idx)
        except Exception as e:
            print(f"  [vision] anthropic failed slide {slide_idx}: {e}", file=sys.stderr)
            return []

    # --- Gemini native ---
    if env_provider == "gemini":
        key = env_api_key or gemini_key
        if not key:
            return None
        # Prefer google-genai SDK if installed; else fall back to raw REST (no extra dep)
        try:
            import importlib
            if importlib.util.find_spec("google.genai") is not None:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=key)
                resp = client.models.generate_content(
                    model=_model_for("gemini", "gemini-2.0-flash"),
                    contents=[types.Content(parts=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_bytes(data=base64.b64decode(b64), mime_type="image/png"),
                    ])],
                    config=types.GenerateContentConfig(response_mime_type="application/json", max_output_tokens=700),
                )
                text = resp.text or ""
                return parse_llm_json(text, slide_idx)
        except Exception as e:
            # fall through to REST
            print(f"  [vision] gemini SDK failed, trying REST: {e}", file=sys.stderr)
        try:
            import urllib.request, urllib.error
            mname = _model_for("gemini", "gemini-2.0-flash")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mname}:generateContent?key={key}"
            body = json.dumps({
                "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/png", "data": b64}}]}],
                "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 700}
            }).encode()
            req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode())
            # extract text from candidates
            text = ""
            try:
                text = j["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                text = json.dumps(j)
            return parse_llm_json(text, slide_idx)
        except Exception as e:
            print(f"  [vision] gemini REST failed slide {slide_idx}: {e}", file=sys.stderr)
            return []

    # --- OpenAI / OpenAI-compatible (OpenAI, OpenRouter, Ollama, Gemini OpenAI-compat, etc.) ---
    if env_provider in ("openai", "openai-compatible", "generic", "vllm", "ollama", "openrouter"):
        key = env_api_key or openai_key or os.environ.get("OPENROUTER_API_KEY")
        base = env_base_url or os.environ.get("OPENAI_BASE_URL")
        if not key and not base:
            return None
        try:
            import openai
            kwargs = {"api_key": key or "sk-placeholder"}
            if base:
                kwargs["base_url"] = base
            client = openai.OpenAI(**kwargs)
            resp = client.chat.completions.create(
                model=_model_for("openai", "gpt-4o-mini"),
                max_tokens=600,
                messages=[{"role":"user","content":[
                    {"type":"text","text": prompt},
                    {"type":"image_url","image_url":{"url": f"data:image/png;base64,{b64}"}}
                ]}],
                response_format={"type":"json_object"}
            )
            text = resp.choices[0].message.content
            return parse_llm_json(text, slide_idx)
        except Exception as e:
            print(f"  [vision] openai-compatible failed slide {slide_idx} (provider={env_provider} base={base or 'api.openai.com'}): {e}", file=sys.stderr)
            return []

    # no provider matched
    return None

def parse_llm_json(text, slide_idx):
    # extract JSON object
    try:
        j = json.loads(text)
    except:
        # try to find { ... }
        import re
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return []
        j = json.loads(m.group(0))
    out=[]
    for iss in j.get("issues",[]):
        out.append({"level":"warn","kind": iss.get("kind","VISION"), "detail": f"slide {slide_idx} · {iss.get('detail','')}", "score": j.get("score"), "llm": True})
    return out

def find_free_port():
    with socketserver.TCPServer(("127.0.0.1", 0), socketserver.BaseRequestHandler) as s:
        return s.server_address[1]

async def capture_slides(html_file, out_dir):
    from pyppeteer import launch
    abs_path = os.path.abspath(html_file)
    docroot = os.path.commonpath([os.getcwd(), abs_path])
    # docroot must contain both cwd and file; fallback to ROOT
    if not os.path.isdir(docroot):
        docroot = str(ROOT)
    url_path = os.path.relpath(abs_path, docroot)

    port = find_free_port()
    cwd = os.getcwd()
    os.chdir(docroot)
    httpd = socketserver.TCPServer(("127.0.0.1", port), http.server.SimpleHTTPRequestHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    browser = await launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
    page = await browser.newPage()
    await page.setViewport({"width":1920,"height":1080})
    try:
        await page.goto(f"http://127.0.0.1:{port}/{url_path}", waitUntil="networkidle0", timeout=90000)
        await asyncio.sleep(2)
        # force fonts
        try:
            await page.evaluate("""async () => {
              await Promise.all(['400','500','600','700','800','900'].map(w => document.fonts.load(`${w} 16px Montserrat`)));
              await document.fonts.ready;
            }""")
        except: pass
        await asyncio.sleep(1)
        n = await page.evaluate("() => document.querySelectorAll('section').length || 1")
        if n == 0:
            n=1
        pngs=[]
        # Use element screenshots — robust across viewport/page coordinate quirks
        els = await page.querySelectorAll("section")
        if not els:
            # fallback single capture
            path = os.path.join(out_dir, "slide-01.png")
            await page.screenshot({"path": path, "clip": {"x":0,"y":0,"width":1920,"height":1080}})
            pngs.append(path)
        else:
            for i, el in enumerate(els):
                path = os.path.join(out_dir, f"slide-{i+1:02d}.png")
                await el.screenshot({"path": path})
                pngs.append(path)
    finally:
        await browser.close()
        httpd.shutdown()
        os.chdir(cwd)
    return pngs

async def run(html_file, brand, use_vision, strict, out_path, vision_provider=None, vision_model=None, vision_api_key=None, vision_base_url=None):
    tmpdir = tempfile.mkdtemp(prefix="vision-qa-")
    pngs = await capture_slides(html_file, tmpdir)
    print(f"captured {len(pngs)} slide(s) → {tmpdir}")

    brand_rgb = parse_brand(brand)
    all_findings=[]
    for idx, png in enumerate(pngs, start=1):
        findings = analyze_slide(png, brand_rgb, idx)
        for f in findings:
            print(f"  {f['level'].upper():4} [{f['kind']}] {f['detail']}")
        all_findings.extend(findings)

        if use_vision:
            print(f"  [vision] slide {idx}: querying LLM...")
            llm_findings = await call_vision_llm(png, idx, provider=vision_provider, model=vision_model, api_key=vision_api_key, base_url=vision_base_url)
            if llm_findings is None:
                print(f"  [vision] no API key — skipping LLM (heuristics only). Set GEMINI_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY / VISION_API_KEY, or VISION_BASE_URL for a compatible endpoint.")
                use_vision=False  # don't retry every slide
            else:
                for f in llm_findings:
                    print(f"  WARN [VISION:{f['kind']}] {f['detail']}")
                all_findings.extend(llm_findings)

    # summary
    fails = [f for f in all_findings if f["level"]=="fail"]
    warns = [f for f in all_findings if f["level"]=="warn"]
    print(f"\nheuristic: {len(fails)} fail, {len(warns)} warn across {len(pngs)} slide(s)")
    if out_path:
        report={"file": os.path.abspath(html_file), "brand": brand, "slides": len(pngs), "findings": all_findings, "tmpdir": tmpdir}
        Path(out_path).write_text(json.dumps(report, indent=2))
        print(f"report → {out_path}")

    # exit code: heuristics fail -> 1. With --strict, any warn -> 1. LLM never fails alone unless strict.
    has_fail = len(fails) > 0
    has_warn = len(warns) > 0
    if has_fail or (strict and has_warn):
        print("RESULT: FAIL — vision gate" if has_fail else "RESULT: FAIL — vision gate (--strict)")
        return 1
    if has_warn:
        print("RESULT: PASS (with warnings)")
        return 0
    print("RESULT: PASS — vision clean")
    return 0

def main():
    p=argparse.ArgumentParser(description="Design Engine Vision QA — perceptual gate (Phase 4)")
    p.add_argument("file", help="HTML file (deck / flyer / carousel)")
    p.add_argument("--brand", default="neutral", help="brand palette: neutral|livefree|fyp or comma hex list")
    p.add_argument("--vision", action="store_true", help="also query vision LLM if API key is set (auto-detects GEMINI/ANTHROPIC/OPENAI)")
    p.add_argument("--vision-provider", default=None, help="vision provider: auto|anthropic|openai|gemini|openrouter|ollama|generic (default auto)")
    p.add_argument("--vision-model", default=None, help="vision model id (e.g. gemini-2.0-flash, gpt-4o-mini, claude-3-5-sonnet-latest)")
    p.add_argument("--vision-api-key", default=None, help="API key (or set GEMINI_API_KEY/ANTHROPIC_API_KEY/OPENAI_API_KEY/VISION_API_KEY)")
    p.add_argument("--vision-base-url", default=None, help="OpenAI-compatible base URL (e.g. https://openrouter.ai/api/v1)")
    p.add_argument("--strict", action="store_true", help="warnings become failures")
    p.add_argument("--out", default=None, help="write JSON report to path")
    args=p.parse_args()
    if not os.path.exists(args.file):
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(2)
    try:
        import PIL, numpy
    except ImportError:
        print("Need Pillow + numpy: pip install Pillow numpy", file=sys.stderr)
        sys.exit(2)
    code = asyncio.get_event_loop().run_until_complete(run(args.file, args.brand, args.vision, args.strict, args.out, args.vision_provider, args.vision_model, args.vision_api_key, args.vision_base_url))
    sys.exit(code)

if __name__=="__main__":
    main()
