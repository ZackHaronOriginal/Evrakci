/* Mockup helper shared by the six tab pages (mockup only; Qt builds the same shell natively).
 * 1. Reads ?theme=light|dark|hc, ?hc=aquatic|desert|dusk|nightsky, ?text=130|150 and ?state=<name>
 *    and sets them on <html>. data-large marks every text step from 130 % up (one threshold).
 *    The states a page offers are listed in <html data-states="main,menu,…">; the first is default.
 * 2. Shows elements whose data-in lists the state, hides those whose data-out lists it.
 * 3. Builds the title band (<header class="titlebar" data-tab="kontrol">) and the status bar's
 *    job item (<span data-job>) so all six pages share one shell.
 * 4. Renders the Lucide icons (icons.js).
 * 5. Draws the thin scrollbar on every scroll area with more content (headless Chromium hides
 *    real scrollbars; Qt shows a 6 px QScrollBar) and fades the cut edge, so a cut line always
 *    reads as "more below".
 */
(function () {
  const q = new URLSearchParams(location.search);
  const root = document.documentElement;
  for (const key of ["theme", "hc", "text", "state"]) if (q.get(key)) root.dataset[key] = q.get(key);
  if (Number(root.dataset.text) >= 130) root.dataset.large = "";
  const states = (root.dataset.states || "main").split(",");
  if (!root.dataset.state) root.dataset.state = states[0];
  const state = root.dataset.state;
  document.querySelectorAll("[data-in]").forEach(el => { el.hidden = !el.dataset.in.split(",").includes(state); });
  document.querySelectorAll("[data-out]").forEach(el => { if (el.dataset.out.split(",").includes(state)) el.hidden = true; });

  const TABS = [["yukle", "Yükle"], ["kontrol", "Kontrol"], ["sablonlar", "Şablonlar"],
                ["degerler", "Değerler"], ["disa-aktar", "Dışa Aktar"], ["rehber", "Rehber"]];
  document.querySelectorAll("header.titlebar[data-tab]").forEach(h => {
    const on = h.dataset.tab;
    h.innerHTML =
      '<img class="logo" src="../../../logo/kit/evrakci-app-icon.svg" alt="">' +
      '<button class="iconbtn sm menubtn' + (h.dataset.menu ? " on" : "") + '" aria-label="Menü (Alt)" title="Menü (Alt)"><i class="ic" data-i="menu"></i></button>' +
      '<nav class="tabs" role="tablist" aria-label="Sekmeler">' +
      TABS.map(([id, label], i) => `<div class="tab${id === on ? " on" : ""}" role="tab" aria-selected="${id === on}" title="${label} (Ctrl+${i + 1})">${label}</div>`).join("") +
      "</nav>" +
      '<div class="drag" aria-hidden="true"></div>' +
      '<div class="search" role="button" aria-label="Komut ara (Ctrl+K)"><i class="ic" data-i="search"></i>Ara<span class="k">Ctrl+K</span></div>' +
      '<div class="caption" aria-hidden="true"><span><i class="ic" data-i="minus"></i></span><span><i class="ic" data-i="square"></i></span><span><i class="ic" data-i="x"></i></span></div>';
  });
  document.querySelectorAll("[data-job]").forEach(el => {
    const none = el.dataset.job === "none";
    el.style.display = "contents";
    el.innerHTML = none
      ? '<span class="item job" title="İş aç: son işler"><i class="ic" data-i="folder-open"></i>İş açılmadı<i class="ic" data-i="chevron-down"></i></span>'
      : '<span class="item job" title="İşi değiştir: son işler"><i class="ic" data-i="folder-open"></i>Kasım 2026 kapasite raporları<i class="ic" data-i="chevron-down"></i></span>' +
        `<span class="item saved" data-p="2"><i class="ic" data-i="check"></i>${el.dataset.jobWhat ? el.dataset.jobWhat + " kaydedildi" : "Kaydedildi"} ${el.dataset.job || "14:32"}</span>`;
  });
  /* the logo symbol (docs/logo/kit/evrakci-symbol-*.svg geometry), one colour from --brand-mark */
  const SYMBOL = '<svg viewBox="0 0 256 256" aria-hidden="true" fill="currentColor">' +
    ["M44 51l14-25h36l14 25z", "M96 121l14-25h36l14 25z", "M148 191l14-25h36l14 25z"].map(d => `<path d="${d}"/>`).join("") +
    [50, 120, 190].map(y => `<rect x="32" y="${y}" width="192" height="40" rx="9"/>`).join("") + "</svg>";
  document.querySelectorAll(".brandmark").forEach(el => { el.innerHTML = SYMBOL; });
  if (typeof renderIcons === "function") renderIcons();

  /* 5. scroll cue: thumb + bottom fade on scroll areas that hold more than they show */
  const drawScrollCues = () => {
    const win = document.querySelector(".window");
    if (!win) return;
    win.querySelectorAll(".sbar").forEach(n => n.remove());
    const wr = win.getBoundingClientRect();
    for (const el of win.querySelectorAll("*")) {
      if (el.closest("[hidden], [data-clip-ok]")) continue;
      const oy = getComputedStyle(el).overflowY;
      if ((oy !== "auto" && oy !== "scroll") || el.scrollHeight <= el.clientHeight + 1) continue;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      const below = el.scrollTop + el.clientHeight < el.scrollHeight - 1;
      el.classList.toggle("more-below", below);
      const h = Math.max(24, r.height * el.clientHeight / el.scrollHeight);
      const top = (r.height - h) * el.scrollTop / (el.scrollHeight - el.clientHeight);
      const bar = document.createElement("i");
      bar.className = "sbar";
      bar.setAttribute("aria-hidden", "true");
      bar.style.cssText = `left:${r.right - wr.left - 5}px;top:${r.top - wr.top + top + 2}px;height:${h - 4}px`;
      win.appendChild(bar);
    }
  };
  window.drawScrollCues = drawScrollCues;

  /* toast anchor (one rule on every tab): bottom-right of the work layer, 12 px in, above the
     status bar. When the tab has an inspector, the toast is laid out in the inspector column right
     above its foot (Qt: inserted into the inspector's layout, not floating), so the scroll area
     shrinks instead of anything being covered: not the primary, the table or the page. */
  const placeToasts = () => {
    document.querySelectorAll(".layer > .toast").forEach(t => {
      if (t.hidden) return;
      const foot = [...t.parentElement.querySelectorAll(".inspector > .ins-foot")].find(f => !f.closest("[hidden]") && f.getBoundingClientRect().width);
      if (foot) { foot.parentElement.insertBefore(t, foot); t.classList.add("in-inspector"); }
    });
  };
  window.placeToasts = placeToasts;
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => requestAnimationFrame(() => { placeToasts(); drawScrollCues(); }));
})();
