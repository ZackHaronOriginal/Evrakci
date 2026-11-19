"""Final spec: render every tab mockup to PNG and report layout problems.

Usage:
    python3 docs/ui-goal/mockups/final/_render.py                  # every *.html here, all states
    python3 docs/ui-goal/mockups/final/_render.py kontrol.html     # only the named pages
    python3 docs/ui-goal/mockups/final/_render.py --themes light   # fewer themes (default light,dark,hc)
    python3 docs/ui-goal/mockups/final/_render.py --no-text150     # skip the 130 % and 150 % text passes
    python3 docs/ui-goal/mockups/final/_render.py --sheets         # also write png/_sheet-<name>-<state>.png

Each page lists its states in <html data-states="main,menu,…">. Every state is opened as
<page>?state=<state>&theme=<theme> at 1366x768 (deviceScaleFactor 1) and written as
png/<name>[-<state>]-<theme>.png (the first state has no state suffix). The text passes add
?text=130 and ?text=150 in light and write png/<name>[-<state>]-<130|150>-light.png. The first
state of each page is also rendered in the Windows 11 "Desert" contrast theme (a light HC
palette): png/<name>-hc-desert.png.

Checks (each printed as a WARNING line, GOAL.md 3.3):
  clip      an element with overflow hidden/clip whose content is larger than its box
  ellipsis  text cut with text-overflow: ellipsis
  spill     text that runs out of its cell, button, field or tab (overflow visible, so it overlaps)
  scroll-x  a scroll container that needs sideways scrolling
  outside   a visible element that sticks out of the 1366x768 window (outside any clipping box)
  tiny      UI text below the 13 px floor (D4); paper drawings (.pg, .crop, .paper) are scans, exempt
  overlap   a popover, toast, tooltip or read-out that covers the selected or edited table row, a
            status cell (status word or rider in a table) or a filled primary button
  stale     (end of run) a contact sheet older than one of the renders it shows
Elements inside [data-clip-ok] (a scroll viewport that stands for more content, e.g. the
timeline) are skipped for clip only. Kontrol also reports gate 7: the share of the timeline
viewport covered by page pixels.

Needs the Python Playwright package and its preinstalled Chromium; it never downloads browsers.
"""
from __future__ import annotations

import glob
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "png"
VIEWPORT = {"width": 1366, "height": 768}

CHECK_SCRIPT = """
() => {
  const found = [];
  const win = document.querySelector('.window');
  const wr = win.getBoundingClientRect();
  const describe = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.classList.length) s += '.' + [...el.classList].join('.');
    const text = (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 48);
    return text ? `${s} "${text}"` : s;
  };
  const visible = (el) => {
    if (el.closest('[hidden]')) return false;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const hidden = v => v === 'hidden' || v === 'clip';
  const SPILL = ['td', 'th', '.btn', '.field', '.cmd', '.tab', '.sel-item', '.gtab', '.rider', '.mi', '.kv .v', '.item', '.toast', '.tip'];
  for (const el of win.querySelectorAll('*')) {
    if (el.closest('svg') || !visible(el)) continue;
    const cs = getComputedStyle(el);
    const dx = el.scrollWidth - el.clientWidth, dy = el.scrollHeight - el.clientHeight;
    if (!el.closest('[data-clip-ok]')) {
      if (hidden(cs.overflowX) && dx > 1) found.push(`clip x +${dx}px  ${describe(el)}`);
      if (hidden(cs.overflowY) && dy > 1) found.push(`clip y +${dy}px  ${describe(el)}`);
    }
    if (cs.textOverflow === 'ellipsis' && dx > 1) found.push(`ellipsis  ${describe(el)}`);
    if (SPILL.some(sel => el.matches(sel)) && !hidden(cs.overflowX) && el.scrollWidth > el.clientWidth + 1)
      found.push(`spill +${el.scrollWidth - el.clientWidth}px  ${describe(el)}`);
    if ((cs.overflowX === 'auto' || cs.overflowX === 'scroll') && dx > 1) found.push(`scroll-x +${dx}px  ${describe(el)}`);
    const clipped = (() => {  // inside a box that clips or scrolls: the clip / scroll-x checks cover it
      for (let a = el.parentElement; a && a !== win; a = a.parentElement) {
        const s = getComputedStyle(a);
        if (s.overflowX !== 'visible' || s.overflowY !== 'visible') return true;
      }
      return false;
    })();
    if (!clipped && !el.closest('[data-clip-ok]') && !el.closest('.pg, .crop, .paper')) {
      const r = el.getBoundingClientRect();
      if (r.right > wr.right + 0.5 || r.bottom > wr.bottom + 0.5 || r.left < wr.left - 0.5 || r.top < wr.top - 0.5)
        found.push(`outside  ${describe(el)}`);
    }
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && !el.closest('.pg, .crop, .paper, [data-paper]') && parseFloat(cs.fontSize) < 12.95)
      found.push(`tiny ${cs.fontSize}  ${describe(el)}`);
  }
  const OVER = ['.tip', '.toast', '.menu', '.palette', '.readout'];
  const KEEP = ['tr.cur', 'td.edit', 'td .st', 'td .rider', '.btn.primary'];
  const overlays = [...win.querySelectorAll(OVER.join(','))].filter(visible);
  const keep = [...win.querySelectorAll(KEEP.join(','))].filter(visible);
  for (const o of overlays) {
    const a = o.getBoundingClientRect();
    for (const k of keep) {
      if (o.contains(k)) continue;
      const b = k.getBoundingClientRect();
      const w = Math.min(a.right, b.right) - Math.max(a.left, b.left), h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (w > 1 && h > 1) found.push(`overlap ${Math.round(w)}x${Math.round(h)}px  ${describe(o)}  covers  ${describe(k)}`);
    }
  }
  return [...new Set(found)];
}
"""

GATE7_SCRIPT = """
() => {
  const tl = document.querySelector('[data-measure="timeline"]');
  if (!tl || tl.closest('[hidden]')) return null;
  const r = tl.getBoundingClientRect();
  let area = 0;
  for (const p of tl.querySelectorAll('.slot .pg')) {
    const q = p.getBoundingClientRect();
    const w = Math.max(0, Math.min(q.right, r.right) - Math.max(q.left, r.left));
    const h = Math.max(0, Math.min(q.bottom, r.bottom) - Math.max(q.top, r.top));
    area += w * h;
  }
  const w = document.querySelector('.slot .pg');
  return {share: area / (r.width * r.height), thumb: w ? [w.offsetWidth, w.offsetHeight] : null};
}
"""


def launch(p):
    """Launch Playwright's Chromium; if its pinned build is missing, use any preinstalled one."""
    try:
        return p.chromium.launch()
    except Exception as error:  # noqa: BLE001 - version mismatch with the preinstalled browsers
        root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
        candidates = sorted(glob.glob(f"{root}/chromium_headless_shell-*/*/chrome-headless-shell")
                            + glob.glob(f"{root}/chromium-*/*/chrome"), reverse=True)
        if not candidates:
            raise SystemExit(f"No Chromium found under {root}: {error}") from error
        return p.chromium.launch(executable_path=candidates[0])


def states_of(html: Path) -> list[str]:
    match = re.search(r'data-states="([^"]+)"', html.read_text(encoding="utf-8"))
    return match.group(1).split(",") if match else ["main"]


def shoot(page, html: Path, state: str, first: bool, theme: str, text: str | None,
          hc: str | None = None) -> tuple[Path, list[str], dict | None]:
    query = f"?state={state}&theme={theme}" + (f"&text={text}" if text else "") + (f"&hc={hc}" if hc else "")
    page.goto(html.as_uri() + query)
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(330)  # let the 180/240 ms pop-in animations settle
    name = (html.stem + ("" if first else f"-{state}") + (f"-{text}" if text else "") + f"-{theme}"
            + (f"-{hc}" if hc else "") + ".png")
    out = OUT / name
    page.locator(".window").first.screenshot(path=str(out))
    return out, page.evaluate(CHECK_SCRIPT), page.evaluate(GATE7_SCRIPT)


def sheet(page, files: list[Path], out: Path) -> None:
    """2x2 contact sheet at half size: light, dark, hc, 150 % light."""
    cells = "".join(f'<img src="{f.as_uri()}" style="width:683px;height:384px;display:block">' for f in files)
    page.set_content(f'<body style="margin:0;display:grid;grid-template-columns:683px 683px;background:#888">{cells}</body>')
    page.wait_for_timeout(100)
    page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1366, "height": 768})


def stale_sheets() -> list[str]:
    """Contact sheets older than any render they show (README §9 relies on them for dark and hc)."""
    found = []
    for sheet_png in sorted(OUT.glob("_sheet-*.png")):
        stem = sheet_png.stem[len("_sheet-"):]
        page_name, _, state = stem.rpartition("-")
        html = HERE / f"{page_name}.html"
        if not html.exists():
            found.append(f"stale  {sheet_png.name}: no page {html.name}")
            continue
        first = states_of(html)[0] == state
        base = page_name + ("" if first else f"-{state}")
        sources = [OUT / f"{base}-{t}.png" for t in ("light", "dark", "hc")] + [OUT / f"{base}-150-light.png"]
        for src in sources:
            if not src.exists() or src.stat().st_mtime > sheet_png.stat().st_mtime + 0.5:
                found.append(f"stale  {sheet_png.name} is older than {src.name}; run with --sheets")
                break
    return found


def main() -> int:
    argv = sys.argv[1:]
    themes = ["light", "dark", "hc"]
    if "--themes" in argv:
        themes = argv[argv.index("--themes") + 1].split(",")
        del argv[argv.index("--themes"):argv.index("--themes") + 2]
    flags = {a for a in argv if a.startswith("--")}
    names = [a for a in argv if not a.startswith("--")]
    pages = [HERE / a for a in names] if names else sorted(HERE.glob("*.html"))
    OUT.mkdir(exist_ok=True)
    warnings = 0
    with sync_playwright() as p:
        browser = launch(p)
        context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1, locale="tr-TR")
        page = context.new_page()
        page.on("console", lambda m: m.type == "error" and print(f"  console error: {m.text}"))
        page.on("pageerror", lambda e: print(f"  page error: {e}"))
        for html in pages:
            states = states_of(html)
            for i, state in enumerate(states):
                shots = []
                runs = [(t, None, None) for t in themes]
                runs += [] if "--no-text150" in flags else [("light", "130", None), ("light", "150", None)]
                runs += [("hc", None, "desert")] if i == 0 and "hc" in themes else []
                for theme, text, hc in runs:
                    out, found, gate = shoot(page, html, state, i == 0, theme, text, hc)
                    if not hc and text != "130":
                        shots.append(out)
                    print(f"wrote {out.relative_to(HERE)}")
                    if (theme == themes[0] or text) and not hc:  # layout is theme-independent; check light + 130 + 150
                        scope = f"{html.name} [{state}]" + (f" @{text}%" if text else "")
                        for line in found:
                            print(f"  WARNING {scope}: {line}")
                            warnings += 1
                        if gate:
                            print(f"  gate 7 {scope}: page pixels {gate['share'] * 100:.1f} % of the timeline, thumb {gate['thumb']}")
                if "--sheets" in flags and len(shots) == 4:
                    sheet(page, shots, OUT / f"_sheet-{html.stem}-{state}.png")
        browser.close()
    if not names:  # a full run: every contact sheet must be newer than the renders it shows
        for line in stale_sheets():
            print(f"  WARNING {line}")
            warnings += 1
    print(f"{warnings} warning(s)")
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
