"""The Rehber text: the shipped guide (docs/tarama-rehberi.md) as sections, the shortcut table
generated from the action registry, the HTML the reader shows, and Turkish-folded search.

Nothing here touches widgets, so it is tested on its own.
"""

from __future__ import annotations

import html
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from evrakci.pipeline.ocr.models import app_dir
from evrakci.ui import actions

KEYS_TITLE = "Kısayollar"
# A's empty state: "Sık aranan konular: ayıraç, çözünürlük, zımba, makbuz".
COMMON_TOPICS = ("ayıraç", "çözünürlük", "zımba", "makbuz")
_WORDS_PER_MINUTE = 180
NOTE_TEXT = "Ctrl+F ile rehberde arayın, Ctrl+tekerlek ile yazıyı büyütün."
NOTE_DISMISS = "Bir daha gösterme"
KEYS_LEAD = "Bu sekmede geçerli tuşlar. Diğer sekmelerin tuşları için {sheet} tuşuna basın."
MISSING = "# Tarama rehberi\n\nRehber dosyası bulunamadı."


def guide_text() -> str:
    """The scanning guide shipped with the app (docs/tarama-rehberi.md)."""
    here = Path(__file__).resolve()
    bundle = app_dir()  # the installed app ships docs/ next to evrakci-arayuz.exe
    folders = [bundle / "docs"] if bundle is not None else []
    folders += [here.parents[3] / "docs"]  # a source checkout
    for folder in folders:
        path = folder / "tarama-rehberi.md"
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return MISSING


# -- the model -----------------------------------------------------------------------------
@dataclass
class Block:
    kind: str  # h3, p, ul, ol, table
    items: list = field(default_factory=list)  # inline-markdown strings; table: list of rows


@dataclass
class Section:
    id: str
    title: str
    blocks: list[Block] = field(default_factory=list)


@dataclass
class Guide:
    title: str
    lead: str
    sections: list[Section]

    def titles(self) -> list[str]:
        return [s.title for s in self.sections]

    def words(self) -> int:
        count = len(self.title.split()) + len(self.lead.split())
        for section in self.sections:
            count += len(section.title.split())
            for block in section.blocks:
                for item in block.items:
                    cells = item if isinstance(item, list) else [item]
                    count += sum(len(str(cell).split()) for cell in cells)
        return count

    def minutes(self) -> int:
        return max(1, math.ceil(self.words() / _WORDS_PER_MINUTE))


_NUMBERED = re.compile(r"^\s*\d+\.\s+")
_BULLET = re.compile(r"^\s*[-*]\s+")
_HEADING_NUMBER = re.compile(r"^\d+\.\s*")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", actions.fold(text)).strip("-") or "bolum"


def parse_guide(markdown: str) -> Guide:
    """The small Markdown subset the guide uses: #, ##, ###, lists, one table, paragraphs."""
    title, lead = "Tarama rehberi", ""
    sections: list[Section] = []
    section: Section | None = None
    block: Block | None = None
    lead_parts: list[str] = []

    def add(kind: str) -> Block:
        nonlocal block
        block = Block(kind)
        if section is not None:
            section.blocks.append(block)
        return block

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if block is not None and block.kind == "p":
                block = None
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            block = None
        elif line.startswith("## "):
            name = _HEADING_NUMBER.sub("", line[3:].strip())
            section = Section(_slug(name), name)
            sections.append(section)
            block = None
        elif line.startswith("### ") and section is not None:
            add("h3").items.append(line[4:].strip())
            block = None
        elif line.lstrip().startswith("|") and section is not None:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                continue
            if block is None or block.kind != "table":
                add("table")
            block.items.append(cells)  # type: ignore[union-attr]
        elif (_NUMBERED.match(line) or _BULLET.match(line)) and section is not None:
            kind = "ol" if _NUMBERED.match(line) else "ul"
            if block is None or block.kind != kind:
                add(kind)
            block.items.append(_NUMBERED.sub("", _BULLET.sub("", line)).strip())  # type: ignore[union-attr]
        elif line.startswith(" ") and block is not None and block.kind in ("ul", "ol"):
            block.items[-1] += " " + line.strip()
        elif section is None:
            lead_parts.append(line.strip())
        else:
            if block is None or block.kind != "p":
                add("p").items.append(line.strip())
            else:
                block.items[-1] += " " + line.strip()
    lead = " ".join(lead_parts)
    return Guide(title, lead, sections)


# -- the shortcut table, from the registry -------------------------------------------------
@dataclass(frozen=True)
class KeyRow:
    keys: list[str]  # shown joined with " ve "
    does: str


def _first(keys: list[str]) -> str:
    """The plainest key: the first without the numeric keypad."""
    return next((k for k in keys if "Num" not in k), keys[0]) if keys else ""


def shortcut_rows() -> list[KeyRow]:
    """The keys that matter on Rehber, read from `actions.shortcut_sheet("rehber")` so the table
    never drifts from the real bindings. Rows whose command is not bound are left out."""
    sheet = {(r.group, r.text): r.keys for r in actions.shortcut_sheet("rehber")}

    def keys(group: str, text: str) -> list[str]:
        return sheet.get((group, text), [])

    plan: list[tuple[list[list[str]], str]] = [
        ([keys("Yardım", "Yardım konuları")], "Yardım konularını aç"),
        ([keys("Git", "Rehber")], "Rehber sekmesine geç"),
        ([keys("Düzen", "Bul")], "Rehberde ara"),
        ([keys("Düzen", "Sonraki sonuç"), keys("Düzen", "Önceki sonuç")],
         "Sonraki ve önceki sonuç"),
        ([keys("Rehber", "Aramayı temizle")], "Aramayı temizle"),
        ([keys("Görünüm", "Yakınlaştır"), keys("Görünüm", "Uzaklaştır")],
         "Yazıyı büyüt ve küçült (Ctrl+tekerlek de çalışır)"),
        ([keys("Rehber", "Ayıraç sayfasını yazdır")], "Ayıraç sayfasını yazdır"),
        ([keys("Yardım", "Klavye kısayolları")], "Klavye kısayollarını göster"),
        ([keys("Yardım", "Komut ara")], "Komut ara"),
    ]
    rows = []
    for groups, does in plan:
        if all(groups):
            rows.append(KeyRow([_first(g) for g in groups], does))
    return rows


def sheet_key() -> str:
    """The key that opens the shortcut sheet, for the sentence under "Kısayollar"."""
    return _first([actions.key_text(k) for k in actions.spec("app.kisayollar").shortcuts])


def with_shortcuts(guide: Guide) -> Guide:
    """The guide plus its "Kısayollar" section (unless the Markdown already has one)."""
    if any(s.title == KEYS_TITLE for s in guide.sections):
        return guide
    section = Section(_slug(KEYS_TITLE), KEYS_TITLE)
    section.blocks.append(Block("p", [KEYS_LEAD.format(sheet=f"**{sheet_key()}**")]))
    table = Block("table", [["Kısayol", "Ne yapar"]])
    table.items += [[" ve ".join(f"**{k}**" if i == 0 else k for i, k in enumerate(r.keys)),
                     r.does] for r in shortcut_rows()]
    section.blocks.append(table)
    return Guide(guide.title, guide.lead, [*guide.sections, section])


# -- HTML for QTextBrowser -----------------------------------------------------------------
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class Look:
    """Colours and sizes of the page, taken from the theme by the screen (no literals here)."""

    text: str
    text_2: str
    stroke: str
    stroke_soft: str
    well: str
    accent: str
    body: int  # px at the current text size and zoom
    caption: int
    section: int
    page: int
    gap: tuple[int, int, int, int, int]  # s1 s2 s3 s4 s6, scaled with the zoom
    row: int
    mono: str = "Cascadia Mono, Consolas, monospace"


def inline(text: str, look: Look) -> str:
    out = html.escape(text, quote=False)
    out = _CODE.sub(lambda m: f'<span style="font-family:{look.mono}; font-size:{look.caption}px;'
                              f' background-color:{look.well};">&nbsp;{m.group(1)}&nbsp;</span>',
                    out)
    return _BOLD.sub(lambda m: f'<b style="font-weight:600;">{m.group(1)}</b>', out)


def _block_html(block: Block, look: Look) -> str:
    s1, s2, s3, _s4, _s6 = look.gap
    if block.kind == "h3":
        return (f'<p style="margin-top:{s3 + s1}px; margin-bottom:{s1}px; font-weight:600;'
                f' font-size:{look.body}px;">{inline(block.items[0], look)}</p>')
    if block.kind == "p":
        return (f'<p style="margin-top:{s2}px; margin-bottom:0;">'
                f"{inline(block.items[0], look)}</p>")
    if block.kind in ("ul", "ol"):
        items = "".join(f'<li style="margin-bottom:{s1}px;">{inline(i, look)}</li>'
                        for i in block.items)
        return f'<{block.kind} style="margin-top:0; margin-bottom:0;">{items}</{block.kind}>'
    head, *rows = block.items
    border = f"border-bottom:1px solid {look.stroke};"
    cells = "".join(
        f'<th align="left" style="{border} color:{look.text_2}; font-size:{look.caption}px;'
        f' font-weight:600; padding:{s2}px {s3}px {s2}px 0;">{html.escape(c)}</th>' for c in head)
    first = ' width="38%"'
    pad = max(s1, (look.row - round(look.body * 1.35)) // 2)  # A: 40 px rows
    body = ""
    for row in rows:
        tds = "".join(
            f'<td style="border-bottom:1px solid {look.stroke_soft}; padding:{pad}px {s3}px'
            f' {pad}px 0;"{first if i == 0 else ""}>{inline(c, look)}</td>'
            for i, c in enumerate(row))
        body += f"<tr>{tds}</tr>"
    return (f'<table width="100%" cellspacing="0" cellpadding="0" style="margin-top:{s2}px;">'
            f"<tr>{cells}</tr>{body}</table>")


def guide_html(guide: Guide, look: Look, note: bool = True) -> str:
    """The whole article. Headings carry anchors `bolum-<slug>` for the contents list."""
    s1, s2, s3, s4, s6 = look.gap
    parts = [f'<body style="color:{look.text}; font-size:{look.body}px;">',
             f'<h1 style="margin-top:0; margin-bottom:{s1}px; font-size:{look.page}px;'
             f' font-weight:600;">{html.escape(guide.title)}</h1>']
    if guide.lead:
        parts.append(f'<p style="margin-top:0; margin-bottom:{s4}px; color:{look.text_2};">'
                     f"{inline(guide.lead, look)}</p>")
    if note:
        parts.append(
            f'<table width="100%" cellspacing="0" cellpadding="{s3}"'
            f' bgcolor="{look.well}" style="margin-top:{s4}px;"><tr>'
            f'<td width="{look.body}"><img src="rehber:info" width="{look.body}"'
            f' height="{look.body}"></td><td>{html.escape(NOTE_TEXT)}</td>'
            f'<td align="right"><a href="rehber:gizle" style="color:{look.accent};'
            f' font-weight:600; text-decoration:none;">{html.escape(NOTE_DISMISS)}</a>'
            f"</td></tr></table>")
    for section in guide.sections:
        parts.append(
            f'<h2 id="bolum-{section.id}" style="margin-top:{s6}px; margin-bottom:{s2}px;'
            f' font-size:{look.section}px; font-weight:600;">'
            f'<a name="bolum-{section.id}"></a>{html.escape(section.title)}</h2>')
        parts += [_block_html(b, look) for b in section.blocks]
    parts.append("</body>")
    return "".join(parts)


# -- search --------------------------------------------------------------------------------
def fold_with_map(text: str) -> tuple[str, list[int]]:
    """Turkish-folded `text` (İ/i, I/ı, accents) and, per folded char, its index in `text`."""
    folded: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        piece = actions.fold(char)
        folded.append(piece)
        origin.extend([index] * len(piece))
    return "".join(folded), origin


def find_in_text(text: str, query: str) -> list[tuple[int, int]]:
    """(start, length) of every non-overlapping match of `query` in `text`, folded."""
    needle = actions.fold(query.strip())
    if not needle:
        return []
    haystack, origin = fold_with_map(text)
    found: list[tuple[int, int]] = []
    at = haystack.find(needle)
    while at != -1:
        start = origin[at]
        end = origin[at + len(needle) - 1] + 1
        found.append((start, end - start))
        at = haystack.find(needle, at + len(needle))
    return found


Finder = Callable[[str], list[tuple[int, int]]]
