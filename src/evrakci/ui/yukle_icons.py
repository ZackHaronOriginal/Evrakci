"""Two Lucide icons of the Yükle mockup that lucide.py does not carry yet (see below)."""

from evrakci.ui import icons, lucide

# Lucide 0.460.0 icons (ISC) of final-a that lucide.py does not carry yet, from final-a/icons.js.
# TODO(foundation): add "loader-circle" and "scan-line" to tools/build_lucide.py NAMES.
EXTRA_ICONS = {
    "loader-circle": '<path d="M21 12a9 9 0 1 1-6.219-8.56" />',
    "scan-line": '<path d="M3 7V5a2 2 0 0 1 2-2h2" /> <path d="M17 3h2a2 2 0 0 1 2 2v2" /> '
                 '<path d="M21 17v2a2 2 0 0 1-2 2h-2" /> <path d="M7 21H5a2 2 0 0 1-2-2v-2" /> '
                 '<path d="M7 12h10" />',
}
for _name, _markup in EXTRA_ICONS.items():
    if _name not in lucide.ICONS:
        icons.PATHS.setdefault(_name, _markup)
