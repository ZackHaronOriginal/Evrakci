"""final-a fidelity gate: prove that nothing direction A drew has changed.

Usage (from this folder, after `python3 _render.py`):
    python3 _fidelity.py

1. EXACT. kontrol and degerler, default state, light and dark: the new render in png/ must be
   pixel-identical to ../directions/a/png/. Any differing pixel is a FAIL (count + bounding box).
2. CHROME. All six tabs, default state, light, against ../directions/a/png/kontrol-light.png:
   - logo            x 0-48, y 0-44: identical
   - right of tabs   job name + Kaydedildi, search, ≡, caption buttons (x from A's .tb-right to
                     1366, y 0-44): identical
   - drag gap        between the tab strip and the job name, y 0-44: identical
   - tabs            every tab that is selected in neither image and sits at the same place must be
                     identical; only A's selected tab (Kontrol) and the page's selected tab may differ
                     (the semibold label of the selected tab can shift the tabs after it by a
                     subpixel; a shifted unselected tab is compared at its own position)
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
        a, b = a.crop(box), b.crop(box)
    d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v else 0)
    bbox = d.getbbox()
    if bbox and box:
        bbox = (bbox[0] + box[0], bbox[1] + box[1], bbox[2] + box[0], bbox[3] + box[1])
    return (sum(1 for v in d.getdata() if v) if bbox else 0), bbox


def measure(page, html: Path) -> dict:
    page.goto(html.as_uri())
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(200)
    return page.evaluate(MEASURE)


rows: list[tuple[str, str, str, str]] = []


def check(scope: str, name: str, count: int, bbox, judged: bool = True) -> bool:
    ok = count == 0
    verdict = ("PASS" if ok else "FAIL") if judged else "info"
    rows.append((scope, name, verdict, "identical" if ok else f"{count} px differ, bbox {bbox}"))
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
        good &= check(scope, "logo x0-48 y0-44", *diff(img, ref, (0, 0, 48, 44)))
        same_right = abs(dom["right"][0] - a_dom["right"][0]) < 0.01
        if not same_right:
            rows.append((scope, "job/search/≡/caption", "FAIL", f"moved: x {dom['right'][0]:.2f} vs A {a_dom['right'][0]:.2f}"))
            good = False
        else:
            good &= check(scope, "job/search/≡/caption", *diff(img, ref, (a_right, 0, W, 44)))
        nav_end = int(max(dom["nav"][2], a_dom["nav"][2])) + 9
        good &= check(scope, "drag gap", *diff(img, ref, (nav_end, 0, a_right, 44)))
        sel = next(t["r"] for t in dom["tabs"] if t["on"])
        bad_tabs, shifted = [], []
        for i, (t_new, t_old) in enumerate(zip(dom["tabs"], a_dom["tabs"])):
            if t_new["on"] or t_old["on"]:
                continue
            if t_new["r"] == t_old["r"]:
                n, bb = diff(img, ref, tuple(int(round(v)) for v in t_new["r"]))
            else:  # shifted by the selected tab's semibold label: compare the tab at its own place
                shifted.append(i)
                bn = tuple(int(round(v)) for v in t_new["r"])
                bo = tuple(int(round(v)) for v in t_old["r"])
                n, bb = diff(img.crop(bn), ref.crop(bo).resize((bn[2] - bn[0], bn[3] - bn[1])))
            if n:
                bad_tabs.append(f"tab {i + 1}: {n} px")
        label = "unselected tabs" + (f" ({len(shifted)} shifted)" if shifted else "")
        rows.append((scope, label, "FAIL" if bad_tabs else "PASS", ", ".join(bad_tabs) or "identical"))
        good &= not bad_tabs
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
