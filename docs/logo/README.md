# Evrakçı logo

![Kit overview](kit-overview.png)

**Idea:** three filed documents seen from above, their guide tabs at the left, centre and right:
the same three positions Evrakçı uses for its three kinds of cut (QR separator, filter, manual).
In colour the middle tab is signal orange, the app's "needs a check" rider.

The kit is built from one geometry by `build_kit.py` (`python3 docs/logo/build_kit.py`), which
also writes the PNG exports and updates the app copies: `packaging/linux/evrakci.svg`,
`packaging/evrakci.ico` and `src/evrakci/ui/logo_data.py` (window icon). It needs fontTools,
Pillow and PySide6, and the Inter Display font (`fonts-inter` on Debian/Ubuntu).
Earlier concepts (A, B and C drafts) are kept in `concepts/` for reference.

## Files (`kit/`)

| File | Use |
|---|---|
| `evrakci-app-icon.svg` | App icon: Windows exe/installer, Linux menu, window and taskbar |
| `evrakci-app-icon-16.svg` | Pixel-grid cut of the app icon, used at 24 px and below |
| `evrakci-symbol-colour.svg` | Symbol on light backgrounds (green files, orange middle tab) |
| `evrakci-symbol-green.svg` / `-black.svg` / `-white.svg` | One-colour symbol: brand green, black, reversed |
| `evrakci-symbol-16.svg` | Pixel-grid symbol for 16 px |
| `evrakci-horizontal-colour.svg` | Main lockup on light backgrounds |
| `evrakci-horizontal-on-green.svg` | Lockup on cabinet green (manila files, white name) |
| `evrakci-horizontal-black.svg` / `-white.svg` | One-colour lockups |
| `evrakci-stacked-colour.svg` / `-black.svg` | Stacked lockup for square spaces |
| `png/` | PNG exports: app icon 16–256 px, lockups at 1200 px, symbol at 1024 px |

## Colours

| Role | Hex | RGB | Token (DESIGN.md) |
|---|---|---|---|
| Cabinet green | `#3f5a4c` | 63 90 76 | `shell` |
| Manila | `#e9d9a6` | 233 217 166 | `manila` |
| Signal orange | `#e8731a` | 232 115 26 | `rider` |
| Ink | `#1d2a23` | 29 42 35 | `ink` |

Orange appears only on the middle tab. One-colour versions drop it; the shape still reads.

## Wordmark

"Evrakçı" in Inter Display SemiBold (SIL Open Font License 1.1), converted to outlines, tracking
−1 %, with the font's own kerning. The cap height is 118/256 of the symbol height in the
horizontal lockup and the name sits on the symbol's optical centre.

## Clear space and minimum size

- **Clear space:** at least the height of one card (40/256 of the symbol, about 16 %) on all sides.
- **Minimum size:** symbol 16 px (use the `-16` cuts at 24 px and below); horizontal lockup 96 px
  wide on screen, 25 mm in print.

## Don't

- Don't recolour the tabs (orange is only for the middle tab and only means "needs a check").
- Don't change tab positions, add a fourth card, or rotate, skew, outline or add shadows.
- Don't set the name in another font or put the colour symbol on busy or mid-tone backgrounds;
  use the one-colour versions there.
- Don't place the colour lockup on green; use `horizontal-on-green`.

Trademark clearance has not been checked; do a professional search before registering it.
