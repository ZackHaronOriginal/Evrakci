"""Lucide icons of the Dışa Aktar mockup that lucide.py does not carry yet (see below)."""

from evrakci.ui import icons, lucide

# Lucide 0.460.0 icons (ISC) from final-a/icons.js.
# TODO(foundation): add these five to tools/build_lucide.py NAMES; this module can then go.
EXTRA_ICONS = {
    "loader-circle": '<path d="M21 12a9 9 0 1 1-6.219-8.56" />',
    "ban": '<circle cx="12" cy="12" r="10" /> <path d="m4.9 4.9 14.2 14.2" />',
    "braces": '<path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1" /> '
              '<path d="M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1"'
              ' />',
    "folder-check": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 '
                    '3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" /> '
                    '<path d="m9 13 2 2 4-4" />',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2" /> '
            '<path d="M7 11V7a5 5 0 0 1 10 0v4" />',
}
for _name, _markup in EXTRA_ICONS.items():
    if _name not in lucide.ICONS:
        icons.PATHS.setdefault(_name, _markup)
