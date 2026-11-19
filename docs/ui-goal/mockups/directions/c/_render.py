"""Render the direction C mockups (copied from ../../_render.py) to PNG and report clipped content.

Usage:
    python3 docs/ui-goal/mockups/_render.py                 # every *.html in this folder
    python3 docs/ui-goal/mockups/_render.py kontrol.html    # only the named pages
    python3 docs/ui-goal/mockups/_render.py --themes light,dark,hc
    python3 docs/ui-goal/mockups/_render.py --no-text150      # skip the 150 % text pass

Every page is also rendered once at 150 % text (first state, light) as png/<name>-150-light.png,
and kontrol + degerler once in the high-contrast preview (<name>-*-hc.png); the clipping check
covers both (GOAL 3.3).

Each page is opened at 1366x768, deviceScaleFactor 1, once per theme (data-theme on <html>).
A page may hold several window states: every element matching `.window[data-state]` is shot
on its own. The first state is written as png/<name>-<theme>.png, the others as
png/<name>-<state>-<theme>.png. Pages without `.window` are shot as the 1366x768 viewport.

Clipping check: every element whose computed overflow (x or y) is hidden/clip and whose
content is larger than its box (scrollWidth > clientWidth + 1 or scrollHeight >
clientHeight + 1) is printed as a warning. Elements marked data-clip-ok are skipped.
Text that is cut with text-overflow: ellipsis is reported too: nothing may be elided at
the default size (GOAL.md §3.3).

Needs the Python Playwright package (pip install playwright) and its preinstalled Chromium;
it never downloads browsers.
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "png"
VIEWPORT = {"width": 1366, "height": 768}

CLIP_SCRIPT = """
(root) => {
  const found = [];
  const describe = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    if (el.classList.length) s += '.' + [...el.classList].join('.');
    const state = el.closest('[data-state]');
    if (state) s = '[' + state.dataset.state + '] ' + s;
    const text = (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 50);
    return text ? `${s} "${text}"` : s;
  };
  for (const el of root.querySelectorAll('*')) {
    if (el.closest('[data-clip-ok]') || el.closest('svg')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const hidden = v => v === 'hidden' || v === 'clip';
    const dx = el.scrollWidth - el.clientWidth, dy = el.scrollHeight - el.clientHeight;
    if (hidden(cs.overflowX) && dx > 1) found.push(`x +${dx}px  ${describe(el)}`);
    if (hidden(cs.overflowY) && dy > 1) found.push(`y +${dy}px  ${describe(el)}`);
    if (cs.textOverflow === 'ellipsis' && dx > 1 && !hidden(cs.overflowX)) found.push(`ellipsis  ${describe(el)}`);
  }
  return found;
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


# Extra checks (review round 1): at the default text size no scroll container may need sideways
# scrolling (a table that scrolls sideways at 100 % hides a column), and every menu-bar access key
# must be an ASCII letter other than I and unique in its bar (Turkish Q keyboard, GOAL 3.1).
EXTRA_SCRIPT = """
(args) => {
  const [root, checkScroll] = args;
  const found = [];
  for (const el of root.querySelectorAll('*')) {
    if (!checkScroll || el.closest('[data-clip-ok]') || el.closest('svg')) continue;
    const cs = getComputedStyle(el);
    if ((cs.overflowX === 'auto' || cs.overflowX === 'scroll') && el.scrollWidth > el.clientWidth + 1) {
      const st = el.closest('[data-state]');
      found.push(`sideways scroll +${el.scrollWidth - el.clientWidth}px  [${st ? st.dataset.state : ''}] ${el.className}`);
    }
  }
  for (const bar of root.querySelectorAll('.menubar')) {
    const keys = [...bar.querySelectorAll('u')].map(u => u.textContent.trim().toUpperCase());
    for (const k of keys) if (!/^[A-HJ-Z]$/.test(k)) found.push(`menu access key "${k}" is not ASCII A-Z without I`);
    if (new Set(keys).size !== keys.length) found.push(`menu access keys repeat: ${keys.join(',')}`);
  }
  return [...new Set(found)];
}
"""

HC_PAGES: set[str] = set()   # direction C: HC follows the OS palette in Qt; not previewed here


def render(page, html: Path, themes: list[str], text: str | None = None, only_first: bool = False) -> int:
    """Shoot every state of one page per theme. With text="150" the page is opened at 150 % text
    (mockup.js reads ?text=) and only the first state is written, as <name>-150-<theme>.png."""
    warnings = 0
    for theme in themes:
        page.goto(html.as_uri() + (f"?text={text}" if text else ""))
        page.evaluate("t => { document.documentElement.dataset.theme = t; }", theme)
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(350)  # let the 180 ms pop-in animations settle
        windows = page.locator(".window[data-state]")
        count = windows.count()
        targets = [(windows.nth(i), windows.nth(i).get_attribute("data-state")) for i in range(count)]
        if not targets:
            targets = [(None, None)]
        if only_first:
            targets = targets[:1]
        for index, (element, state) in enumerate(targets):
            suffix = f"-{state}" if index and state else ""
            if text:
                suffix += f"-{text}"
            out = OUT / f"{html.stem}{suffix}-{theme}.png"
            if element is None:
                page.screenshot(path=str(out))
            else:
                element.screenshot(path=str(out))
            print(f"wrote {out.relative_to(HERE)}")
        if theme == themes[0]:  # layout does not change with theme; check once
            scope = f"{html.name} @{text}%" if text else html.name
            root = targets[0][0].element_handle() if only_first and targets[0][0] else page.locator("body").element_handle()
            for line in page.evaluate(CLIP_SCRIPT, root):
                print(f"  CLIPPING WARNING {scope}: {line}")
                warnings += 1
            for line in page.evaluate(EXTRA_SCRIPT, [root, not text]):
                print(f"  LAYOUT WARNING {scope}: {line}")
                warnings += 1
    return warnings


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    themes = ["light", "dark"]
    for a in sys.argv[1:]:
        if a.startswith("--themes="):
            themes = a.split("=", 1)[1].split(",")
    if "--themes" in sys.argv:
        themes = sys.argv[sys.argv.index("--themes") + 1].split(",")
        args = [a for a in args if a != sys.argv[sys.argv.index("--themes") + 1]]
    pages = [HERE / a for a in args] if args else sorted(HERE.glob("*.html"))
    OUT.mkdir(exist_ok=True)
    warnings = 0
    with sync_playwright() as p:
        browser = launch(p)
        context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1, locale="tr-TR")
        page = context.new_page()
        page.on("console", lambda m: m.type == "error" and print(f"  console error: {m.text}"))
        page.on("pageerror", lambda e: print(f"  page error: {e}"))
        for html in pages:
            warnings += render(page, html, themes)
            if html.stem in HC_PAGES and "hc" not in themes:
                warnings += render(page, html, ["hc"])
            if "--no-text150" not in sys.argv:
                warnings += render(page, html, ["light"], text="150", only_first=True)
        browser.close()
    print(f"{warnings} clipping warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
