"""final-a (direction A as approved, additions only): render every page and state to PNG and
report clipped content. A's clipping and layout checks are unchanged.

Usage:
    python3 _render.py                       # every *.html in this folder
    python3 _render.py kontrol.html          # only the named pages
    python3 _render.py --themes light,dark   # default: light,dark,hc
    python3 _render.py --no-text150          # skip the 150 % text pass

Each page lists its states in <html data-states="main,…">; the first is the default and is A's
own drawing. Every state is opened as <page>.html?state=<state> at 1366x768, deviceScaleFactor 1,
once per theme (data-theme on <html>), plus once at 150 % text in light (?text=150).
Output: png/<name>[-<state>]-<theme>.png and png/<name>[-<state>]-150-light.png
(the default state has no -<state> part, so png/kontrol-light.png is A's kontrol-light.png).

Clipping check: every element whose computed overflow (x or y) is hidden/clip and whose
content is larger than its box (scrollWidth > clientWidth + 1 or scrollHeight >
clientHeight + 1) is printed as a warning. Elements marked data-clip-ok are skipped.
Text that is cut with text-overflow: ellipsis is reported too: nothing may be elided at
the default size (GOAL.md §3.3). Hidden elements (other states) are skipped.

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
    if (cs.display === 'none' || cs.visibility === 'hidden' || el.closest('[hidden]')) continue;
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
    # Headless Chromium hides scrollbars by default; the mockups draw Windows 11's thin scrollbar
    # on the scroll areas that exist (150 % panes, the Rehber article), so let them show.
    try:
        return p.chromium.launch(ignore_default_args=["--hide-scrollbars"])
    except Exception as error:  # noqa: BLE001 - version mismatch with the preinstalled browsers
        root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
        candidates = sorted(glob.glob(f"{root}/chromium_headless_shell-*/*/chrome-headless-shell")
                            + glob.glob(f"{root}/chromium-*/*/chrome"), reverse=True)
        if not candidates:
            raise SystemExit(f"No Chromium found under {root}: {error}") from error
        return p.chromium.launch(executable_path=candidates[0], ignore_default_args=["--hide-scrollbars"])


# Cut-text check (review round 4): the overflow check above only sees boxes whose own content
# overflows, so text cut by an ANCESTOR (a pane with overflow: hidden marked data-clip-ok, or a
# scroll area) went unreported (kontrol @150 %: "71 Silinec"). For every visible text run this
# intersects the client boxes of all its clipping/scrolling ancestors and warns when the run is
# partly inside and partly outside (fully outside = scrolled out of view, which is fine).
#   - cut by an overflow: hidden/clip edge  -> WARNING: that text can never be read.
#   - cut only by the edge of a scroll area -> "scroll edge" info line, not a warning: the run is
#     reachable by scrolling, as in any QScrollArea / QTableView, and the area shows a scrollbar.
# It also warns when a position: sticky element in the same scroll area (pinned buttons) covers
# part of a text run that it does not contain: text half under a button looks broken. Text drawn
# on a scanned page (.pg, .sheet, .lp-page, .crop or [data-scan]) is image content and is
# skipped; so are hidden states.
CUT_SCRIPT = r"""
(root) => {
  const found = [], TOL = 1;
  const visible = el => { for (let e = el; e && e !== document.body; e = e.parentElement) {
      if (e.hidden) return false; const cs = getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') return false; } return true; };
  const clips = v => v !== 'visible';
  const inter = (a, b) => ({ l: Math.max(a.l, b.l), t: Math.max(a.t, b.t), r: Math.min(a.r, b.r), b: Math.min(a.b, b.b) });
  const describe = (el, text) => {
    let s = el.tagName.toLowerCase();
    if (el.classList.length) s += '.' + [...el.classList].join('.');
    return `${s} "${text.slice(0, 40)}"`;
  };
  const stickies = [...root.querySelectorAll('*')].filter(e => getComputedStyle(e).position === 'sticky' && visible(e));
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const text = n.textContent.replace(/\s+/g, ' ').trim();
    const el = n.parentElement;
    if (!text || !el || el.closest('svg, script, style, .pg, .sheet, .lp-page, .crop, [data-scan]') || !visible(el)) continue;
    const range = document.createRange(); range.selectNodeContents(n);
    const rects = [...range.getClientRects()].filter(r => r.width > 0 && r.height > 0);
    if (!rects.length) continue;
    const t = { l: Math.min(...rects.map(r => r.left)), t: Math.min(...rects.map(r => r.top)),
                r: Math.max(...rects.map(r => r.right)), b: Math.max(...rects.map(r => r.bottom)) };
    let clip = { l: -1e9, t: -1e9, r: 1e9, b: 1e9 }, hard = { ...clip }, soft = { ...clip }, scroller = null;
    for (let a = el.parentElement; a; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (cs.position === 'fixed') break;
      if (clips(cs.overflowX) || clips(cs.overflowY)) {
        const b = a.getBoundingClientRect();
        const box = { l: b.left + a.clientLeft, t: b.top + a.clientTop, r: b.left + a.clientLeft + a.clientWidth, b: b.top + a.clientTop + a.clientHeight };
        clip = inter(clip, { l: clips(cs.overflowX) ? box.l : -1e9, r: clips(cs.overflowX) ? box.r : 1e9,
                             t: clips(cs.overflowY) ? box.t : -1e9, b: clips(cs.overflowY) ? box.b : 1e9 });
        const hx = /hidden|clip/.test(cs.overflowX), hy = /hidden|clip/.test(cs.overflowY);
        hard = inter(hard, { l: hx ? box.l : -1e9, r: hx ? box.r : 1e9, t: hy ? box.t : -1e9, b: hy ? box.b : 1e9 });
        const sx = /auto|scroll/.test(cs.overflowX), sy = /auto|scroll/.test(cs.overflowY);
        soft = inter(soft, { l: sx ? box.l : -1e9, r: sx ? box.r : 1e9, t: sy ? box.t : -1e9, b: sy ? box.b : 1e9 });
        if (!scroller && /auto|scroll/.test(cs.overflowX + cs.overflowY)) scroller = a;
      }
    }
    const i = inter(clip, t);
    const outside = i.r <= i.l || i.b <= i.t;
    const within = c => t.l >= c.l - TOL && t.r <= c.r + TOL && t.t >= c.t - TOL && t.b <= c.b + TOL;
    const edge = c => t.b > c.b + TOL ? 'bottom' : t.t < c.t - TOL ? 'top' : t.r > c.r + TOL ? 'right' : 'left';
    const key = el;
    if (!outside && !within(clip) && !seen.has(key)) {
      seen.add(key);
      /* a side is a hard cut when an overflow: hidden edge on that side is tighter than every
         scroll-area edge (a scroll area flush with its hidden card counts as the scroll area) */
      const sides = [['l', t.l < clip.l - TOL], ['r', t.r > clip.r + TOL], ['t', t.t < clip.t - TOL], ['b', t.b > clip.b + TOL]];
      const tighter = k => (k === 'l' || k === 't') ? hard[k] > soft[k] + 0.5 : hard[k] < soft[k] - 0.5;
      const hardSide = sides.find(([k, cut]) => cut && tighter(k));
      const name = { l: 'left', r: 'right', t: 'top', b: 'bottom' };
      found.push(hardSide ? `cut by ${name[hardSide[0]]} edge  ${describe(el, text)}`
                          : `INFO scroll edge (${edge(clip)})  ${describe(el, text)}`);
      continue;
    }
    if (outside || !scroller) continue;
    for (const st of stickies) {
      if (!scroller.contains(st) || st.contains(el)) continue;
      const r = st.getBoundingClientRect(), o = inter({ l: r.left, t: r.top, r: r.right, b: r.bottom }, t);
      const covered = o.r > o.l + TOL && o.b > o.t + TOL;
      const whole = o.l <= t.l + TOL && o.r >= t.r - TOL && o.t <= t.t + TOL && o.b >= t.b - TOL;
      if (covered && !whole && !seen.has(key)) { seen.add(key); found.push(`half under pinned ${st.className}  ${describe(el, text)}`); }
    }
  }
  return found;
}
"""


# Extra checks (review round 1): at the default text size no scroll container may need sideways
# scrolling (a table that scrolls sideways at 100 % hides a column), and every menu-bar access key
# must be an ASCII letter other than I and unique in its bar (Turkish Q keyboard, GOAL 3.1).
EXTRA_SCRIPT = """
(args) => {
  const [root, checkScroll] = args;
  const found = [];
  for (const el of root.querySelectorAll('*')) {
    if (!checkScroll || el.closest('[data-clip-ok]') || el.closest('svg') || el.closest('[hidden]')) continue;
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

def states_of(page, html: Path) -> list[str]:
    page.goto(html.as_uri())
    return (page.evaluate("document.documentElement.dataset.states") or "main").split(",")


def render(page, html: Path, themes: list[str], text: str | None = None) -> int:
    """Shoot every state of one page per theme. With text="150" the page is opened at 150 % text
    (state.js reads ?text=) and written as <name>[-<state>]-150-<theme>.png."""
    warnings = 0
    states = states_of(page, html)
    for index, state in enumerate(states):
        for theme in themes:
            query = [f"state={state}"] + ([f"text={text}"] if text else [])
            page.goto(html.as_uri() + "?" + "&".join(query))
            page.evaluate("t => { document.documentElement.dataset.theme = t; }", theme)
            page.evaluate("document.fonts.ready")
            # Let the 180/240 ms pop-in animations settle AND the compositor drop their layers: at
            # 350 ms (A's wait) the toast's shadow was now and then still composited, which moves
            # antialiased pixels by a colour level. 1000 ms is reproducible.
            page.wait_for_timeout(1000)
            suffix = f"-{state}" if index else ""
            if text:
                suffix += f"-{text}"
            out = OUT / f"{html.stem}{suffix}-{theme}.png"
            # A page screenshot clipped to the window, not locator.screenshot(): the element
            # screenshot scrolls and re-composites first, and Chromium then rasterises antialiased
            # corners and shadows one colour level differently from run to run. The clipped page
            # shot is reproducible, so the default states match direction A's PNGs pixel for pixel
            # (_fidelity.py).
            box = page.evaluate("""() => { const w = document.querySelector('.window');
                if (!w) return null; const r = w.getBoundingClientRect();
                return { x: r.left, y: r.top, width: r.width, height: r.height }; }""")
            page.screenshot(path=str(out), clip=box) if box else page.screenshot(path=str(out))
            print(f"wrote {out.relative_to(HERE)}")
            if theme == themes[0]:  # layout does not change with theme; check once
                scope = f"{html.name}?state={state}" + (f" @{text}%" if text else "")
                root = page.locator("body").element_handle()
                for line in page.evaluate(CLIP_SCRIPT, root):
                    print(f"  CLIPPING WARNING {scope}: {line}")
                    warnings += 1
                for line in page.evaluate(CUT_SCRIPT, root):
                    if line.startswith("INFO "):
                        print(f"  info {scope}: {line[5:]}")
                        continue
                    print(f"  CUT TEXT WARNING {scope}: {line}")
                    warnings += 1
                for line in page.evaluate(EXTRA_SCRIPT, [root, not text]):
                    print(f"  LAYOUT WARNING {scope}: {line}")
                    warnings += 1
    return warnings


def new_page(browser):
    context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1, locale="tr-TR")
    page = context.new_page()
    page.on("console", lambda m: m.type == "error" and print(f"  console error: {m.text}"))
    page.on("pageerror", lambda e: print(f"  page error: {e}"))
    return page


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    themes = ["light", "dark", "hc"]
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
        page = new_page(browser)
        for html in pages:
            warnings += render(page, html, themes)
            if "--no-text150" not in sys.argv:
                warnings += render(page, html, ["light"], text="150")
        browser.close()
    print(f"{warnings} clipping warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
