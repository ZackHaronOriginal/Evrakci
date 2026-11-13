/* final-a mockup helper (addition): places the added popovers against what opens them, so they
 * stay attached at any text size. #hamburger drops from the "≡" button (right-aligned),
 * #submenu flips to its left at the hovered item, #palette drops from the title-band search.
 * At 150 % text the Değerler key hint follows the edited cell (A placed it by hand at 100 %,
 * which is left untouched). Qt anchors QMenu/popups natively. */
(function () {
  const place = () => {
    const win = document.querySelector(".window");
    if (!win) return;
    const w = win.getBoundingClientRect();
    const rel = r => ({ left: r.left - w.left, top: r.top - w.top, right: r.right - w.left, bottom: r.bottom - w.top });
    const ham = document.getElementById("hamburger"), sub = document.getElementById("submenu");
    const btn = document.querySelector('.titlebar .iconbtn.sm[aria-label^="Menü"]');
    if (ham && !ham.hidden && btn) {
      const b = rel(btn.getBoundingClientRect());
      ham.style.top = (b.bottom + 4) + "px";
      ham.style.left = (b.right - ham.offsetWidth) + "px";
      if (sub && !sub.hidden) {
        const h = ham.querySelector(".mi.hov") || ham.querySelector(".mi");
        const hr = rel(h.getBoundingClientRect());
        sub.style.left = (parseFloat(ham.style.left) - sub.offsetWidth + 2) + "px";
        sub.style.top = (hr.top - 5) + "px";
      }
    }
    const pal = document.getElementById("palette"), search = document.querySelector(".titlebar .search");
    if (pal && !pal.hidden && search) {
      const s = rel(search.getBoundingClientRect());
      pal.style.top = (s.bottom + 4) + "px";
      pal.style.left = Math.max(8, s.right - pal.offsetWidth) + "px";
    }
    if (document.documentElement.dataset.text) {
      /* a context menu that no longer fits below flips up, as QMenu does */
      document.querySelectorAll(".layer > .menu").forEach(m => {
        if (m.hidden) return;
        const room = m.offsetParent.clientHeight - 8;
        if (m.offsetTop + m.offsetHeight > room) m.style.top = Math.max(8, room - m.offsetHeight) + "px";
      });
      const hint = document.querySelector(".hint"), cell = document.querySelector("td.edit");
      if (hint && cell && hint.offsetParent) {
        const p = hint.offsetParent.getBoundingClientRect(), c = cell.getBoundingClientRect();
        hint.style.left = (c.left - p.left) + "px";
        hint.style.top = (c.bottom - p.top + 2) + "px";
      }
    }
  };
  place();
  if (document.fonts) document.fonts.ready.then(place);
})();
