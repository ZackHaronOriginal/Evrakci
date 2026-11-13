"""Themes for direction A "Fluent 2 Mica": one ThemeManager over the generated tokens.

`manager()` is the app-wide instance. It resolves the mode (system / light / dark / hc), the
density (compact / normal / comfortable) and the text size (100 / 115 / 130 / 150 %; 130 and up
move the chrome one density up, D5) into colours, sizes, fonts, a QPalette and the stylesheet,
applies them to the app, and emits `changed` after every switch. Values come only from
`tokens.generated` (built from the approved spec's tokens.css).

The old Kartotek module API (TOKENS, colour(), palette(), stylesheet(), FONT_* ...) keeps
working for the screens until Phase 3: old token names map to A's roles through LEGACY.
"""
from __future__ import annotations

import math
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QPalette

from evrakci.ui import motion
from evrakci.ui.tokens import generated as g
from evrakci.ui.tokens import qss

MODES = ("system", "light", "dark", "hc")
DENSITIES = ("compact", "normal", "comfortable")
TEXT_SIZES = tuple(g.TEXT_SCALES)

# Old Kartotek name -> A role (the screens still use these until Phase 3).
LEGACY: dict[str, str] = {
    "shell": "accent", "shell_2": "accent-hover", "shell_3": "accent-hover",
    "on_shell": "text-on-accent", "on_shell_2": "text-on-accent",
    "ground": "base", "card": "layer", "paper": "card", "ink": "text", "ink_2": "text-2",
    "rule": "stroke", "rule_strong": "edge", "control_edge": "edge",
    "manila": "manila", "manila_edge": "manila-edge", "manila_ink": "manila-ink",
    "index_red": "stroke", "rider": "rider", "rider_edge": "rider-edge", "rider_ink": "rider-ink",
    "check_ink": "check-text", "check_wash": "check-wash", "row_cur": "selected",
    "qr": "cut-qr", "filter": "cut-filter", "manual": "cut-manual", "ok": "ok",
    "focus": "focus-outer",
    # Template variables sit on the scan (paper stays light): A's paper-safe hues, no orange.
    "v1": "cut-qr", "v2": "cut-filter", "v3": "on-manila-ok", "v4": "cut-manual",
    "key_cap": "hover", "key_edge": "stroke", "key_edge_on_shell": "accent-hover",
    "disabled_ink": "text-2", "hover": "hover", "rider_on_shell": "rider",
}
VARIABLE_COLOURS = ("v1", "v2", "v3", "v4")
DERIVED = ("text-disabled", "icon-disabled", "accent-disabled", "on-accent-disabled")

FONT_FAMILY = "Inter"  # bundled (fonts.py); QFont falls back when it is not loaded
FONT_SIZE = g.TYPE["body"]["size"]  # px at 100 %
SMALL = g.TYPE["caption"]["size"]  # the 13 px floor (D4)
DISABLED_ALPHA = 0.45  # A: .cmd.dis / .iconbtn.dis opacity
SCROLLBAR_W = 9  # final-a/additions.css: the thin Windows 11 scrollbar

# Component sizes A and additions.css give per density (compact is not drawn: as normal).
COMPONENT = {
    "header-h": (36, 36, 48), "menu-item-h": (34, 34, 48), "rider-h": (22, 22, 30),
    "toast-h": (52, 52, 64), "lg-h": (40, 40, 48), "sep-h": (20, 20, 28), "badge-h": (20, 20, 28),
}

# Font roles: (type step, weight, OpenType features).
FONT_ROLES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "caption": ("caption", "regular", ()),
    "caption-medium": ("caption", "medium", ()),
    "caption-strong": ("caption", "semibold", ()),
    "caption-num": ("caption", "regular", tuple(g.FEATURES["num"])),
    "body": ("body", "regular", ()),
    "body-medium": ("body", "medium", ()),
    "body-strong": ("body", "semibold", ()),
    "num": ("body", "regular", tuple(g.FEATURES["num"])),
    "num-strong": ("body", "semibold", tuple(g.FEATURES["num"])),
    "value": ("body", "regular", tuple(g.FEATURES["value"])),
    "section": ("section", "semibold", ()),
    "panel": ("panel", "semibold", ()),
    "page": ("page", "semibold", tuple(g.FEATURES["num"])),
}


@dataclass(frozen=True)
class TitleBand:
    """Geometry of the title band at the current text size (see title_band_rule)."""

    height: int
    tab_height: int
    tab_labels: str  # "all", or "selected" (unselected tabs show only their icon + tooltip)
    logo: int
    control_height: int  # job switch, search, ≡ button
    search_width: int
    caption_width: int


@dataclass(frozen=True)
class Shadow:
    """One shadow layer (px offsets; QPainter draws it, QSS cannot)."""

    x: int
    y: int
    blur: int
    spread: int
    color: QColor
    inset: bool


def title_band_rule(text_size: int, titlebar_h: int) -> TitleBand:
    """The title band per text size. PROVISIONAL at 150 % (owner decision pending, PROPOSALS
    item 3): additions.css option a, unselected tabs icon-only. Switch the 150 % branch here."""
    if text_size >= 150:
        return TitleBand(titlebar_h, 44, "selected", 24, 40, 196, 46)
    return TitleBand(titlebar_h, 36, "all", 20, 32, 148, 46)


def _px(value: float) -> int:
    return int(math.floor(value + 0.5))


def _blend(fg: str, bg: str, alpha: float) -> str:
    a, b = QColor(fg), QColor(bg)
    mix = [round(x * alpha + y * (1 - alpha)) for x, y in zip(a.getRgb()[:3], b.getRgb()[:3],
                                                               strict=True)]
    return QColor(*mix).name()


def _windows_high_contrast() -> bool | None:
    """SPI_GETHIGHCONTRAST on Windows; None elsewhere or when the call fails."""
    if sys.platform != "win32":
        return None
    import ctypes

    class HIGHCONTRASTW(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwFlags", ctypes.c_uint),
                    ("lpszDefaultScheme", ctypes.c_wchar_p)]

    info = HIGHCONTRASTW()
    info.cbSize = ctypes.sizeof(info)
    if not ctypes.windll.user32.SystemParametersInfoW(0x0042, info.cbSize, ctypes.byref(info), 0):
        return None
    return bool(info.dwFlags & 0x1)  # HCF_HIGHCONTRASTON


def system_high_contrast() -> bool:
    """True when the OS asks for high contrast (Windows SPI, else Qt's contrast hint)."""
    windows = _windows_high_contrast()
    if windows is not None:
        return windows
    app = QGuiApplication.instance()
    hints = app.styleHints() if app is not None else None
    access = getattr(hints, "accessibility", lambda: None)() if hints is not None else None
    if access is None or not hasattr(Qt, "ContrastPreference"):
        return False
    return access.contrastPreference() == Qt.ContrastPreference.HighContrast


def system_dark() -> bool:
    app = QGuiApplication.instance()
    return app is not None and app.styleHints().colorScheme() == Qt.ColorScheme.Dark


def _windows_system_colours() -> dict[str, str]:
    """The live Windows high-contrast colours for the sys-* tokens (empty elsewhere)."""
    if sys.platform != "win32":
        return {}
    import ctypes

    index = {"sys-window": 5, "sys-text": 8, "sys-highlight": 13, "sys-highlight-text": 14,
             "sys-gray": 17, "sys-hotlight": 26}
    out = {}
    for name, i in index.items():
        ref = ctypes.windll.user32.GetSysColor(i)
        out[name] = QColor(ref & 0xFF, (ref >> 8) & 0xFF, (ref >> 16) & 0xFF).name()
    return out


class ThemeManager(QObject):
    """Holds the look settings and turns them into Qt values; `changed` fires after a switch."""

    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._mode = "system"
        self._density = "normal"
        self._text = 100
        self._reduced: bool | None = None
        self._prefs = None
        self._app = None
        self._colors: dict[str, str] | None = None
        self._last_sheet = ""
        self._applying = False

    # -- settings ----------------------------------------------------------------
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode not in MODES:
            raise ValueError(f"Geçersiz tema: {mode!r}")
        self._update("_mode", mode, "set_theme")

    def theme(self) -> str:
        """The theme in use: light, dark or hc ("system" resolved against the OS)."""
        if self._mode != "system":
            return self._mode
        if system_high_contrast():
            return "hc"
        return "dark" if system_dark() else "light"

    def density(self) -> str:
        return self._density

    def set_density(self, density: str) -> None:
        if density not in DENSITIES:
            raise ValueError(f"Geçersiz yoğunluk: {density!r}")
        self._update("_density", density, "set_density")

    def effective_density(self) -> str:
        """The density in use: one step up at text 130 % and 150 % (D5)."""
        step = 1 if self._text >= g.DENSITY_STEP_UP_FROM else 0
        return DENSITIES[min(DENSITIES.index(self._density) + step, len(DENSITIES) - 1)]

    def text_scale(self) -> int:
        return self._text

    def set_text_scale(self, percent: int) -> None:
        if percent not in TEXT_SIZES:
            raise ValueError(f"Geçersiz yazı boyutu: {percent!r}")
        self._update("_text", percent, "set_text_size")

    def reduced_motion(self) -> bool | None:
        """The user's override; None follows the system."""
        return self._reduced

    def set_reduced_motion(self, value: bool | None) -> None:
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"Geçersiz hareket ayarı: {value!r}")
        motion.set_reduced_motion_override(value)
        self._update("_reduced", value, "set_reduced_motion")

    def bind_prefs(self, prefs) -> None:
        """Load the look from `prefs` (evrakci.ui.prefs.Prefs) and save every later change."""
        self._prefs = None
        self._mode, self._density = prefs.theme(), prefs.density()
        self._text, self._reduced = prefs.text_size(), prefs.reduced_motion()
        motion.set_reduced_motion_override(self._reduced)
        self._prefs = prefs
        self._refresh()

    def _update(self, attr: str, value: object, pref_setter: str) -> None:
        if getattr(self, attr) == value:
            return
        setattr(self, attr, value)
        if self._prefs is not None:
            getattr(self._prefs, pref_setter)(value)
        self._refresh()

    def _refresh(self) -> None:
        self._colors = None
        if self._app is not None:
            self.apply(self._app)
        self.changed.emit()

    # -- values ------------------------------------------------------------------
    def colors(self) -> dict[str, str]:
        """Every role (A token, derived and legacy name) as a hex string, for the theme in use."""
        if self._colors is None:
            self._colors = self._build_colors(self.theme())
        return self._colors

    def _build_colors(self, name: str) -> dict[str, str]:
        out = dict(g.COLORS[name])
        if name == "hc":
            system = {**g.SYSTEM_COLORS}
            if system_high_contrast():
                system.update(_windows_system_colours())
            out.update({token: system[ref] for token, ref in g.HC_SYSTEM.items()})
            out.update(system)
            gray = system["sys-gray"]
            out.update({"text-disabled": gray, "icon-disabled": gray,
                        "accent-disabled": out["base"], "on-accent-disabled": gray})
        else:
            layer = out["layer"]
            out["text-disabled"] = _blend(out["text"], layer, DISABLED_ALPHA)
            out["icon-disabled"] = _blend(out["icon"], layer, DISABLED_ALPHA)
            out["accent-disabled"] = _blend(out["accent"], layer, DISABLED_ALPHA)
            out["on-accent-disabled"] = _blend(out["text-on-accent"], out["accent-disabled"],
                                               DISABLED_ALPHA + 0.3)
        out.update({old: out[new] for old, new in LEGACY.items()})
        return out

    def hex(self, role: str) -> str:
        return self.colors()[role]

    def color(self, role: str) -> QColor:
        return QColor(self.hex(role))

    def shadow(self, name: str) -> list[Shadow]:
        """A shadow token ("shadow-float", "shadow-paper", "edge-light") for QPainter."""
        layers = g.SHADOWS[self.theme()][name]
        return [Shadow(s["x"], s["y"], s["blur"], s["spread"], _rgba(s["color"]), s["inset"])
                for s in layers]

    def size(self, name: str) -> int:
        """A size in px at the current density and text size: chrome sizes ("control-h",
        "row-h", ...), spacing ("s4"), radii ("r-layer"), type ("fs-body", "lh-body") and the
        component sizes in COMPONENT ("menu-item-h", ...)."""
        density = self.effective_density()
        if name in g.SIZES[density]:
            return int(g.SIZES[density][name])
        if name in COMPONENT:
            return COMPONENT[name][DENSITIES.index(density)]
        if name in g.SPACE:
            return int(g.SPACE[name])
        if name in g.RADII:
            return int(g.RADII[name])
        kind, _, step = name.partition("-")
        if kind in ("fs", "lh") and step in g.TYPE:
            base = g.TYPE[step]["size" if kind == "fs" else "line"]
            return _px(base * g.TEXT_SCALES[self._text])
        raise KeyError(f"unknown size: {name}")

    def font(self, role: str = "body") -> QFont:
        """A QFont for a type role (FONT_ROLES): Inter stack, scaled px size, weight, features."""
        from evrakci.ui import fonts

        step, weight, features = FONT_ROLES[role]
        font = QFont()
        font.setFamilies(fonts.font_stack())
        font.setStyleHint(QFont.StyleHint.SansSerif)
        font.setPixelSize(self.size(f"fs-{step}"))
        font.setWeight(QFont.Weight(g.WEIGHTS[weight]))
        if step == "page":
            font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 99)  # -0.01em
        for tag in features:
            try:
                font.setFeature(QFont.Tag(tag), 1)  # Qt 6.7+
            except (AttributeError, TypeError):
                pass
        return font

    def title_band(self) -> TitleBand:
        return title_band_rule(self._text, self.size("titlebar-h"))

    def palette(self) -> QPalette:
        """QPalette from the role tokens (system colours in hc)."""
        c = self.colors()
        p = QPalette()
        r = QPalette.ColorRole
        roles = [
            (r.Window, "base"), (r.WindowText, "text"), (r.Base, "card"),
            (r.AlternateBase, "layer"), (r.ToolTipBase, "popover"), (r.ToolTipText, "text"),
            (r.PlaceholderText, "text-2"), (r.Text, "text"), (r.Button, "card"),
            (r.ButtonText, "text"), (r.BrightText, "text-on-accent"), (r.Light, "card"),
            (r.Midlight, "stroke-soft"), (r.Mid, "stroke"), (r.Dark, "edge"), (r.Shadow, "edge"),
            (r.Highlight, "accent"), (r.HighlightedText, "text-on-accent"),
            (r.Link, "text-accent"), (r.LinkVisited, "text-accent"),
        ]
        if hasattr(r, "Accent"):
            roles.append((r.Accent, "accent"))
        for role, token in roles:
            p.setColor(role, QColor(c[token]))
        disabled = QPalette.ColorGroup.Disabled
        for role in (r.Text, r.WindowText, r.ButtonText, r.PlaceholderText):
            p.setColor(disabled, role, QColor(c["text-disabled"]))
        p.setColor(disabled, r.Highlight, QColor(c["accent-disabled"]))
        p.setColor(disabled, r.Button, QColor(c["layer"]))
        p.setColor(disabled, r.Base, QColor(c["layer"]))
        return p

    def qss_values(self) -> dict[str, str]:
        """Every value the stylesheet template uses."""
        from evrakci.ui import fonts, icons

        values = dict(self.colors())
        names = [*g.SIZES["normal"], *COMPONENT, *g.SPACE, *g.RADII,
                 *(f"{k}-{s}" for k in ("fs", "lh") for s in g.TYPE)]
        values.update({n: f"{self.size(n)}px" for n in names})
        band = self.title_band()
        # menu items: 1 px edges + the font's own height + padding = menu-item-h exactly
        menu_pad = max(0, self.size("menu-item-h") - 2 - QFontMetrics(self.font("body")).height())
        px = {
            "control-in-h": self.size("control-h") - 2, "lg-in-h": self.size("lg-h") - 2,
            "rider-in-h": self.size("rider-h") - 2, "toast-in-h": self.size("toast-h") - 2,
            "menu-pad-t": menu_pad // 2, "menu-pad-b": menu_pad - menu_pad // 2,
            "sep-margin-v": (self.size("commandbar-h") - self.size("sep-h")) // 2,
            "scrollbar-w": SCROLLBAR_W, "tb-tab-h": band.tab_height,
            "tb-control-h": band.control_height, "tb-control-h-in": band.control_height - 2,
            "tb-search-w-in": band.search_width - 2,
        }
        values.update({k: f"{v}px" for k, v in px.items()})
        hc = self.theme() == "hc"
        values.update({
            "sel-bg": values["accent" if hc else "selected"],
            "sel-fg": values["text-on-accent" if hc else "text"],
            "hover-edge": values["accent"] if hc else "transparent",
            "hover-stroke": values["accent" if hc else "stroke"],
            "rider-border": "2px" if hc else "1px",
        })
        values["font-family"] = ", ".join(f'"{f}"' for f in fonts.font_stack())
        for key, name, colour, stroke in (
            ("icon-check", "check", "text-on-accent", 3),
            ("icon-minus", "minus", "text-on-accent", 3),
            ("icon-chevron-down", "chevron-down", "text-2", 2),
            ("icon-chevron-up", "chevron-up", "text-2", 2),
        ):
            values[key] = icons.icon_file(name, values[colour], stroke)
        return values

    def stylesheet(self) -> str:
        """The app stylesheet for the current theme, density and text size."""
        return qss.render(self.qss_values())

    def menu_item_height(self) -> int:
        return self.size("menu-item-h")

    # -- applying ------------------------------------------------------------------
    def apply(self, app=None) -> None:
        """Install the style, palette, font and stylesheet on `app` (and follow the OS)."""
        from PySide6.QtWidgets import QApplication

        from evrakci.ui import icons, style

        app = app or QApplication.instance()
        if app is None or self._applying:
            return
        self._applying = True
        try:
            if self._app is not app:
                self._app = app
                self._watch_system(app)
            self._set_color_scheme(app)
            self._colors = None
            for cached in (icons.pixmap, icons.icon):
                cached.cache_clear()
            style.install(app)
            palette, sheet = self.palette(), self.stylesheet()
            app.setPalette(palette)
            app.setFont(self.font("body"))
            if sheet != app.styleSheet():
                for widget in app.topLevelWidgets():  # screens that copied the old sheet
                    if self._last_sheet and widget.styleSheet() == self._last_sheet:
                        widget.setPalette(palette)
                        widget.setStyleSheet(sheet)
                app.setStyleSheet(sheet)
            self._last_sheet = sheet
        finally:
            self._applying = False

    def _set_color_scheme(self, app) -> None:
        hints = app.styleHints()
        if not hasattr(hints, "setColorScheme"):
            return
        if self._mode == "system":
            hints.unsetColorScheme()
        else:
            hints.setColorScheme(Qt.ColorScheme.Light if self._mode == "light"
                                 else Qt.ColorScheme.Dark)

    def _watch_system(self, app) -> None:
        hints = app.styleHints()
        hints.colorSchemeChanged.connect(self._system_changed)
        access = hints.accessibility() if hasattr(hints, "accessibility") else None
        if access is not None and hasattr(access, "contrastPreferenceChanged"):
            access.contrastPreferenceChanged.connect(self._system_changed)

    def _system_changed(self, *_args) -> None:
        if self._mode == "system" and not self._applying:
            self._refresh()


def _rgba(hex8: str) -> QColor:
    colour = QColor(hex8[:7])
    colour.setAlpha(int(hex8[7:9], 16) if len(hex8) == 9 else 255)
    return colour


_manager: ThemeManager | None = None


def manager() -> ThemeManager:
    """The app-wide ThemeManager."""
    global _manager
    if _manager is None:
        _manager = ThemeManager()
    return _manager


# -- the old module API (Kartotek screens) -------------------------------------------------
class _Tokens(Mapping):
    """Live view: TOKENS[name] is the hex value of a role or an old name in the current theme."""

    def __getitem__(self, name: str) -> str:
        return manager().colors()[name]

    def __iter__(self) -> Iterator[str]:
        return iter(manager().colors())

    def __len__(self) -> int:
        return len(manager().colors())


TOKENS: Mapping[str, str] = _Tokens()


def colour(name: str) -> str:
    return TOKENS[name]


def variable_colour(index: int) -> str:
    return TOKENS[VARIABLE_COLOURS[index % len(VARIABLE_COLOURS)]]


def apply_font(app) -> None:
    """The window font (Inter, body size)."""
    app.setFont(manager().font("body"))


def palette() -> QPalette:
    return manager().palette()


def stylesheet() -> str:
    return manager().stylesheet()
