"""final-a fidelity gate: prove that nothing direction A drew has changed.

Usage (from this folder, after `python3 _render.py`):
    python3 _fidelity.py

1. EXACT. kontrol and degerler, default state, light and dark: the new render in png/ must match
   ../directions/a/png/. A pixel counts as differing when any channel differs by more than TOL
   (8/255; invisible antialiasing noise stays below it). Any such pixel is a FAIL (count +
   bounding box); every row also prints the largest channel delta seen.
2. CHROME. All six tabs, default state, light, against ../directions/a/png/kontrol-light.png:
   - title band      y 0-44, compared column by column. Allowed to differ: only the selected-tab
                     highlight, i.e. A's selected tab (Kontrol) and this page's selected tab, each
                     with its 8 px reverse-curve feet. Everything else must be identical and is
                     reported in three parts: the logo (x 0-48), the tab strip (x 48 to A's
                     .tb-right), and job name + Kaydedildi, search, ≡ and caption buttons (A's
                     .tb-right to 1366). Every tab and .tb-right must also sit where A put them.
   - command bar     the 8 px gutters and the layer's 1 px frame on both sides (x 0-12 and
                     1354-1366, y 44-88) and the layer's top edge (y 44) outside the two selected
                     tabs: identical. The buttons between are per tab (reported, not judged).
   - status bar      y 740-768: the left gutter (x 0-20) and the top row (y 740): identical.
                     The items are per tab (reported, not judged).
Tab and band positions are measured from the DOM of A's kontrol.html and of each page.
Exit code 1 on any FAIL.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
A = HERE.parent / "directions" / "a"
PAGES = ["yukle", "kontrol", "sablonlar", "degerler", "disa-aktar", "rehber"]
W, H = 1366, 768
BAND = 44   # title band height (y 0-44)
TOL = 8     # per-channel tolerance (of 255) before a pixel counts as different
MAXDELTA = [0]  # largest channel delta seen by the last diff() call(s)
FOOT = 8    # the selected tab's reverse-curve feet, each side

sys.path.insert(0, str(HERE))
from _render import launch  # noqa: E402  (same Chromium lookup as the renderer)

MEASURE = """() => {
  const r = el => { const b = el.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; };
  return { tabs: [...document.querySelectorAll('.titlebar .tab')].map(t => ({ r: r(t), on: t.classList.contains('on') })),
           nav: r(document.querySelector('.titlebar .tabs')), right: r(document.querySelector('.titlebar .tb-right')) };
}"""


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def diff(a: Image.Image, b: Image.Image, box: tuple[int, int, int, int] | None = None) -> tuple[int, tuple | None]:
    if box:
        if box[2] <= box[0] or box[3] <= box[1]:
            return 0, None  # empty region (e.g. no drag gap): nothing to compare
        a, b = a.crop(box), b.crop(box)
    # A pixel differs only when one channel differs by more than TOL (8/255): Chromium's
    # antialiasing of corners and shadows moves by up to ~5/255 between runs, which no one can see.
    raw = ImageChops.difference(a, b)
    peak = max(hi for _, hi in raw.getextrema())
    channels = [c.point(lambda v: 255 if v > TOL else 0) for c in raw.split()]
    d = channels[0]
    for c in channels[1:]:
        d = ImageChops.lighter(d, c)
    bbox = d.getbbox()
    if bbox and box:
        bbox = (bbox[0] + box[0], bbox[1] + box[1], bbox[2] + box[0], bbox[3] + box[1])
    MAXDELTA[0] = max(MAXDELTA[0], peak)
    return (d.histogram()[255] if bbox else 0), bbox


def masked(a: Image.Image, b: Image.Image, box: tuple[int, int, int, int],
           allowed: list[tuple[int, int]]) -> tuple[int, tuple | None]:
    """diff() over box, ignoring the columns in `allowed` (the selected-tab highlights)."""
    x0, y0, x1, y1 = box
    count, boxes, x = 0, [], x0
    cuts = sorted((max(lo, x0), min(hi, x1)) for lo, hi in allowed if hi > x0 and lo < x1)
    for lo, hi in cuts + [(x1, x1)]:
        if lo > x:
            n, bb = diff(a, b, (x, y0, lo, y1))
            count += n
            if bb:
                boxes.append(bb)
        x = max(x, hi)
    if not boxes:
        return count, None
    return count, (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def measure(page, html: Path) -> dict:
    page.goto(html.as_uri())
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(200)
    return page.evaluate(MEASURE)


rows: list[tuple[str, str, str, str]] = []


def check(scope: str, name: str, count: int, bbox, judged: bool = True) -> bool:
    ok = count == 0
    verdict = ("PASS" if ok else "FAIL") if judged else "info"
    peak = MAXDELTA[0]
    MAXDELTA[0] = 0
    detail = (f"{count} px differ (> {TOL}/255), bbox {bbox}" if not ok
              else "identical" if peak == 0 else f"0 px differ (> {TOL}/255)")
    rows.append((scope, name, verdict, f"{detail}; max channel delta {peak}/255"))
    return ok or not judged


def main() -> int:
    good = True
    # 1. exact
    for name in ("kontrol", "degerler"):
        for theme in ("light", "dark"):
            new, old = HERE / "png" / f"{name}-{theme}.png", A / "png" / f"{name}-{theme}.png"
            if not new.exists():
                rows.append((f"{name}-{theme}", "whole window", "FAIL", "render missing: run _render.py"))
                good = False
                continue
            good &= check(f"{name}-{theme}", "whole window vs A", *diff(load(new), load(old)))

    # 2. chrome
    ref = load(A / "png" / "kontrol-light.png")
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1).new_page()
        a_dom = measure(page, A / "kontrol.html")
        doms = {name: measure(page, HERE / f"{name}.html") for name in PAGES}
        browser.close()
    a_right = int(a_dom["right"][0])
    a_sel = next(t["r"] for t in a_dom["tabs"] if t["on"])
    for name in PAGES:
        png = HERE / "png" / f"{name}-light.png"
        if not png.exists():
            rows.append((f"{name}-light", "chrome", "FAIL", "render missing: run _render.py"))
            good = False
            continue
        img, dom = load(png), doms[name]
        scope = f"{name}-light"
        sel = next(t["r"] for t in dom["tabs"] if t["on"])
        # The selected-tab highlight: the tab itself plus its 8 px Fluent "feet" (::before/::after),
        # for A's selected tab (Kontrol) and for this page's. Only these may differ in the band.
        allowed = [(int(r[0]) - FOOT, int(r[2] + 0.999) + FOOT) for r in (a_sel, sel)]
        same_right = abs(dom["right"][0] - a_dom["right"][0]) < 0.01
        same_tabs = all(abs(t["r"][0] - u["r"][0]) < 0.01 and abs(t["r"][2] - u["r"][2]) < 0.01
                        for t, u in zip(dom["tabs"], a_dom["tabs"]))
        if not same_right:
            rows.append((scope, "job/search/≡/caption", "FAIL", f"moved: x {dom['right'][0]:.2f} vs A {a_dom['right'][0]:.2f}"))
            good = False
        if not same_tabs:
            rows.append((scope, "tab positions", "FAIL", "a tab moved or changed width"))
            good = False
        good &= check(scope, "logo x0-48 y0-44", *masked(img, ref, (0, 0, 48, BAND), allowed))
        good &= check(scope, "tabs (bar selection)", *masked(img, ref, (48, 0, a_right, BAND), allowed))
        if same_right:
            good &= check(scope, "job/search/≡/caption", *masked(img, ref, (a_right, 0, W, BAND), allowed))
        rows.append((scope, "selected tab highlight", "info",
                     f"A: x {allowed[0][0]}-{allowed[0][1]}, this tab: x {allowed[1][0]}-{allowed[1][1]} (may differ)"))
        # command bar frame
        for box, label in (((0, 44, 12, 88), "cmd bar left frame"), ((W - 12, 44, W, 88), "cmd bar right frame")):
            good &= check(scope, label, *diff(img, ref, box))
        spans = sorted([(int(a_sel[0]) - 9, int(a_sel[2]) + 9), (int(sel[0]) - 9, int(sel[2]) + 9)])
        edge = [(12, spans[0][0]), (spans[0][1], spans[1][0]), (spans[1][1], W - 12)]
        n_tot, bbs = 0, []
        for x0, x1 in edge:
            if x1 > x0:
                n, bb = diff(img, ref, (x0, 44, x1, 45))
                n_tot += n
                if bb:
                    bbs.append(bb)
        good &= check(scope, "layer top edge y44", n_tot, bbs or None)
        check(scope, "cmd bar buttons (per tab)", *diff(img, ref, (12, 45, W - 12, 88)), judged=False)
        good &= check(scope, "status gutter x0-20", *diff(img, ref, (0, 740, 20, H)))
        good &= check(scope, "status top row y740", *diff(img, ref, (0, 740, W, 741)))
        check(scope, "status items (per tab)", *diff(img, ref, (20, 741, W, H)), judged=False)

    w = [max(len(r[i]) for r in rows) for i in range(3)]
    print(f"{'render':<{w[0]}}  {'region':<{w[1]}}  {'result':<{w[2]}}  detail")
    print("-" * (sum(w) + 40))
    for r in rows:
        print(f"{r[0]:<{w[0]}}  {r[1]:<{w[1]}}  {r[2]:<{w[2]}}  {r[3]}")
    fails = sum(r[2] == "FAIL" for r in rows)
    print("-" * (sum(w) + 40))
    print(f"{'PASS' if good else 'FAIL'}: {fails} failing check(s), {sum(r[2] == 'PASS' for r in rows)} passing")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
