/* final-a mockup helper (addition; A's pages had one state each).
 * Reads ?state=, ?theme=light|dark|hc and ?text=150 and sets them on <html>.
 * The states a page offers are listed in <html data-states="main,…">; the first is the default
 * and is exactly direction A's drawing. Elements with data-in="a,b" exist only in those states
 * (they carry `hidden` in the markup, so the default render never sees them); data-out="a,b"
 * hides an A element in those states; data-cls="state:class class;state2:class" adds classes.
 * Qt builds these states natively; this file only switches the mockup. */
(function () {
  const q = new URLSearchParams(location.search), root = document.documentElement;
  for (const key of ["theme", "text", "state"]) if (q.get(key)) root.dataset[key] = q.get(key);
  const states = (root.dataset.states || "main").split(",");
  const state = root.dataset.state || states[0];
  root.dataset.state = state;
  const win = document.querySelector(".window");
  if (win) win.dataset.state = state;
  document.querySelectorAll("[data-in]").forEach(el => { el.hidden = !el.dataset.in.split(",").includes(state); });
  document.querySelectorAll("[data-out]").forEach(el => { if (el.dataset.out.split(",").includes(state)) el.hidden = true; });
  document.querySelectorAll("[data-cls]").forEach(el => {
    for (const part of el.dataset.cls.split(";")) {
      const [s, cls] = part.split(":");
      if (s.trim() === state) el.classList.add(...cls.trim().split(/\s+/));
    }
  });
})();
