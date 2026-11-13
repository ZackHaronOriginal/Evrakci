"""The one table of commands: menus, buttons, tooltips, palette and shortcut sheet use it.

Every command is an `ActionSpec`. A `Registry` turns the table into QActions on one window,
keeps only the actions of "app" plus the current tab active (so one key can mean different
things on different tabs), and keeps commands without a handler disabled. Screens hook their
slots with `Registry.connect(id, slot)`.

Keyboard rules (Turkish Q keyboard, see docs/ui-goal/shortcuts.md), checked by `validate()`:
no Ç Ş Ğ İ Ö Ü / ı / I in a shortcut, no Ctrl+Alt (AltGr types characters), and no key used
twice on one tab. "Typing keys" (no Ctrl/Alt and not an F-key: letters, Enter, Del, Space,
arrows, Esc) are dropped from an action while a text field has focus, see `TextFocusGuard`.

`local` shortcuts are handled inside one widget (timeline, canvas, table): they are shown in
tooltips and the shortcut sheet but never bound to the QAction. Such a widget accepts
`QEvent.ShortcutOverride` for its keys if it needs one that an action also uses.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import NamedTuple

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)

Key = str | QKeySequence.StandardKey

TABS: dict[str, str] = {
    "yukle": "Yükle", "kontrol": "Kontrol", "sablonlar": "Şablonlar",
    "degerler": "Değerler", "disa_aktar": "Dışa Aktar", "rehber": "Rehber",
}
CONTEXTS = ("app", *TABS)
MENUS: dict[str, str] = {
    "dosya": "&Dosya", "duzen": "Düz&en", "gorunum": "&Görünüm",
    "git": "Gi&t", "araclar": "&Araçlar", "yardim": "&Yardım",
}
SEPARATOR = None

_TURKISH = set("ÇŞĞİÖÜçşğıöü")
_FKEYS = range(Qt.Key.Key_F1.value, Qt.Key.Key_F35.value + 1)
_MODS = (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
         | Qt.KeyboardModifier.MetaModifier)


# Keys and text
def key_sequence(key: Key) -> QKeySequence:
    """A one-chord QKeySequence for a string or the first binding of a StandardKey."""
    if isinstance(key, QKeySequence.StandardKey):
        bindings = QKeySequence.keyBindings(key)
        return bindings[0] if bindings else QKeySequence()
    return QKeySequence(key)


# Key names Qt prints in English that the Turkish UI names itself (shortcuts.md).
# A's labels read "Alt+Yukarı", "Sonraki sayfa (Sağ)", "Ctrl+Enter", "Önizle (Boşluk)".
_KEY_NAMES = {"Space": "Boşluk", "Up": "Yukarı", "Down": "Aşağı", "Left": "Sol",
              "Right": "Sağ", "Return": "Enter"}


def key_text(key: Key) -> str:
    """The key as the platform shows it (NativeText), with A's Turkish names for Space and the
    arrows ("Boşluk", "Yukarı", "Sol"...) and Return as "Enter"."""
    text = key_sequence(key).toString(QKeySequence.SequenceFormat.NativeText)
    parts = text.split("+")
    if parts and parts[-1] in _KEY_NAMES:
        parts[-1] = _KEY_NAMES[parts[-1]]
    return "+".join(parts)


def is_typing_key(key: Key) -> bool:
    """True for a key a text field would consume: no Ctrl/Alt/Meta and not an F-key."""
    seq = key_sequence(key)
    if seq.isEmpty():
        return False
    combo = seq[0]
    return not (combo.keyboardModifiers() & _MODS) and combo.key().value not in _FKEYS


@dataclass(frozen=True)
class ActionSpec:
    """One command. `text` is the menu label with an & access key."""

    id: str
    text: str
    icon: str | None = None
    shortcuts: tuple[Key, ...] = ()
    context: str = "app"
    menu: str | None = None
    tooltip: str = ""
    single_key: bool = False
    checkable: bool = False
    palette: bool = True
    local: bool = False
    keywords: tuple[str, ...] = ()


def _a(id: str, text: str, icon: str | None, keys: tuple[Key, ...] | str = (), *,
       ctx: str = "app", menu: str | None = None, tip: str = "", local: bool = False,
       checkable: bool = False, palette: bool = True, kw: str = "") -> ActionSpec:
    keys = (keys,) if isinstance(keys, str) else tuple(keys)
    typing = not local and any(is_typing_key(k) for k in keys)
    return ActionSpec(id, text, icon, keys, ctx, menu, tip, typing, checkable, palette, local,
                      tuple(kw.split()))


_TAB_MENU = (  # (tab, menu text, icon)
    ("yukle", "&Yükle", "upload"), ("kontrol", "&Kontrol", "list-checks"),
    ("sablonlar", "Ş&ablonlar", "layout-template"), ("degerler", "Değ&erler", "table-2"),
    ("disa_aktar", "&Dışa Aktar", "download"), ("rehber", "&Rehber", "book"),
)

SPECS: tuple[ActionSpec, ...] = (
    # Uygulama: sekmeler ve bölgeler
    *(_a(f"app.sekme.{tab}", label, icon, f"Ctrl+{n}", menu="git",
         tip=f"{TABS[tab]} sekmesine geç", kw="sekme")
      for n, (tab, label, icon) in enumerate(_TAB_MENU, start=1)),
    _a("app.sonraki_sekme", "&Sonraki sekme", "chevron-right", "Ctrl+Tab", menu="git"),
    _a("app.onceki_sekme", "Ö&nceki sekme", "chevron-left",
       ("Ctrl+Shift+Tab", "Ctrl+Shift+Backtab"), menu="git"),
    _a("app.sonraki_bolge", "Sonraki bölge", None, "F6", kw="odak panel"),
    _a("app.onceki_bolge", "Önceki bölge", None, "Shift+F6", kw="odak panel"),
    _a("app.git", "Belgeye veya sayfaya &git…", "arrow-right-to-line", "Ctrl+G", menu="git",
       kw="sayfa belge numara atla"),
    # Dosya
    _a("app.yeni_is", "&Yeni iş oluştur…", "file-plus", "Ctrl+N", menu="dosya", kw="iş aç"),
    _a("app.dosya_ekle", "Dosya &ekle…", "folder-open", "Ctrl+O", menu="dosya",
       kw="parti pdf tarama aç yükle"),
    _a("yukle.klasor_ekle", "K&lasör ekle…", "folder-plus", ctx="yukle", menu="dosya",
       kw="parti pdf tarama klasör bütün"),
    _a("app.kaydet", "Kayde&t", "save", "Ctrl+S", menu="dosya"),
    _a("app.disa_aktar", "&Dışa aktar…", "download", "Ctrl+E", menu="dosya",
       kw="excel klasör yaz"),
    _a("yukle.gezginde_goster", "Dosya &Gezgini'nde göster", "folder-open", "Ctrl+Shift+O",
       ctx="yukle", menu="dosya", kw="klasör explorer"),
    _a("disa_aktar.index_ac", "index.xlsx'i &aç", "sheet", ctx="disa_aktar", menu="dosya",
       kw="excel dizin liste"),
    _a("disa_aktar.gezginde_goster", "Dosya &Gezgini'nde göster", "folder-open",
       "Ctrl+Shift+O", ctx="disa_aktar", menu="dosya", kw="klasör explorer"),
    _a("rehber.yazdir", "Ayıraç sayfasını ya&zdır…", "printer", "Ctrl+P", ctx="rehber",
       menu="dosya", kw="baskı ayraç"),
    _a("rehber.pdf_ac", "PDF ola&rak aç", "file-text", ctx="rehber", menu="dosya",
       kw="ayraç ayıraç sayfası baskı pdf"),
    _a("disa_aktar.yazdir", "Dizini ya&zdır…", "printer", "Ctrl+P", ctx="disa_aktar",
       menu="dosya", kw="baskı liste"),
    _a("app.isi_kapat", "İşi ka&pat", "x", "Ctrl+W", menu="dosya"),
    _a("app.cikis", "Çı&kış", None, "Ctrl+Q", menu="dosya", kw="kapat uygulama"),
    # Düzen
    _a("app.geri_al", "&Geri al", "undo-2", "Ctrl+Z", menu="duzen", kw="undo"),
    _a("app.yinele", "&Yinele", "redo-2", ("Ctrl+Y", "Ctrl+Shift+Z"), menu="duzen",
       kw="redo"),
    _a("app.bul", "B&ul…", "search", "Ctrl+F", menu="duzen", kw="ara"),
    _a("app.sonraki_sonuc", "Sonraki so&nuç", "chevron-down", "F3", menu="duzen"),
    _a("app.onceki_sonuc", "Önceki s&onuç", "chevron-up", "Shift+F3", menu="duzen"),
    # Görünüm
    _a("app.yakinlastir", "&Yakınlaştır", "zoom-in", ("Ctrl+Num++", "Ctrl++", "Ctrl+="),
       menu="gorunum", kw="büyüt zoom"),
    _a("app.uzaklastir", "&Uzaklaştır", "zoom-out", ("Ctrl+-", "Ctrl+Num+-"),
       menu="gorunum", kw="küçült zoom"),
    _a("app.sigdir", "&Sığdır", "maximize-2", "Ctrl+0", menu="gorunum",
       tip="Sayfaya sığdır", kw="zoom"),
    _a("app.yazi_buyut", "Yazı boyutunu &büyüt", "type", "Ctrl+Shift+Num++",
       menu="gorunum", kw="metin font"),
    _a("app.yazi_kucult", "Yazı boyutunu &küçült", "type", "Ctrl+Shift+Num+-",
       menu="gorunum", kw="metin font"),
    _a("app.tam_ekran", "&Tam ekran", "maximize-2", "F11", menu="gorunum", checkable=True),
    _a("app.yan_panel", "Yan &paneli gizle", "panel-right", "F9", menu="gorunum",
       tip="Ayrıntı panelini gizle", kw="ayrıntı kaynak panel denetçi"),
    _a("app.yenile", "Yenile", "refresh-cw", "F5", tip="Listeyi ve önizlemeyi yenile"),
    # Araçlar ve Yardım
    _a("app.ayarlar", "&Ayarlar…", "settings", "Ctrl+,", menu="araclar",
       kw="tercih tema yazı boyutu yoğunluk saklama"),
    _a("app.yardim", "&Yardım konuları", "help-circle", "F1", menu="yardim", kw="nasıl"),
    _a("app.kisayollar", "Klavye &kısayolları", "keyboard", ("Shift+F1", "Ctrl+/", "?"),
       menu="yardim", kw="tuş kısayol"),
    _a("app.komut_ara", "Komut &ara…", "command", ("Ctrl+K", "Ctrl+Shift+P"),
       menu="yardim", palette=False),
    _a("app.hakkinda", "Evrakçı &hakkında", "info", menu="yardim", kw="sürüm lisans"),

    # Yükle
    _a("yukle.yukari", "Partiyi yuka&rı taşı", "arrow-up", "Alt+Up", ctx="yukle",
       menu="duzen", kw="sırala"),
    _a("yukle.asagi", "Partiyi &aşağı taşı", "arrow-down", "Alt+Down", ctx="yukle",
       menu="duzen", kw="sırala"),
    _a("yukle.cikar", "Partiyi çı&kar", "trash-2", "Del", ctx="yukle", menu="duzen",
       tip="Partiyi çıkar (geri alınabilir)", kw="sil kaldır"),
    _a("yukle.yeniden_adlandir", "Yeniden a&dlandır", "pencil", "F2", ctx="yukle",
       menu="duzen", kw="ad isim"),
    _a("yukle.iptal", "İ&ptal et", "square", "Ctrl+.", ctx="yukle", menu="araclar",
       tip="Okumayı iptal et", kw="durdur"),

    # Kontrol
    _a("kontrol.tumunu_sec", "&Tümünü seç", "check-check", "Ctrl+A", ctx="kontrol",
       menu="duzen"),
    _a("kontrol.secimi_kaldir", "Seçimi &kaldır", "x", "Esc", ctx="kontrol", menu="duzen",
       tip="Seçimi kaldır ya da önizlemeyi kapat"),
    _a("kontrol.kes", "Burada k&es", "scissors", "K", ctx="kontrol", menu="duzen",
       tip="Burada kes / kesimi kaldır", kw="ayır böl kesim"),
    _a("kontrol.birlestir", "Önceki belgeyle &birleştir", "merge", "M", ctx="kontrol",
       menu="duzen", kw="kesimi kaldır"),
    _a("kontrol.saga_dondur", "Sağa &döndür", "rotate-cw", "R", ctx="kontrol",
       menu="duzen", kw="çevir"),
    _a("kontrol.sola_dondur", "So&la döndür", "rotate-ccw", "Shift+R", ctx="kontrol",
       menu="duzen", kw="çevir"),
    _a("kontrol.sil", "Sayfayı &sil", "trash-2", "Del", ctx="kontrol", menu="duzen",
       tip="Sayfayı sil / geri getir (geri alınabilir)", kw="kaldır geri getir"),
    _a("kontrol.onayla", "Belgeyi on&ayla", "circle-check", ("Return", "Enter"),
       ctx="kontrol", menu="duzen", tip="Belgeyi onayla ve sonrakine geç",
       kw="incelendi işaretle"),
    _a("kontrol.filtre", "&Filtre uygula…", "funnel", "F", ctx="kontrol", menu="araclar"),
    _a("kontrol.sablon", "Şablonu &uygula", "layout-template", "T", ctx="kontrol",
       menu="araclar"),
    _a("kontrol.degerlerde_ac", "&Değerlerde aç", "table-2", ctx="kontrol", menu="araclar",
       tip="Bu belgeyi Değerler sekmesinde aç"),
    _a("kontrol.onizle", "Ö&nizle", "eye", "Space", ctx="kontrol", menu="gorunum",
       tip="Sayfayı büyük göster", kw="büyüteç önizleme"),
    _a("kontrol.sonraki_kontrol", "Sonraki kon&trol", "triangle-alert", "N", ctx="kontrol",
       menu="git", kw="şüpheli uyarı"),
    _a("kontrol.onceki_kontrol", "Önceki k&ontrol", "triangle-alert", "Shift+N",
       ctx="kontrol", menu="git", kw="şüpheli uyarı"),
    _a("kontrol.sonraki_incelenmemis", "Sonraki incelen&memiş", "circle-dashed", "U",
       ctx="kontrol", menu="git", kw="incelenmedi"),
    _a("kontrol.sonraki_belge", "Sonraki &belge", "chevron-right", "Ctrl+Right",
       ctx="kontrol", menu="git"),
    _a("kontrol.onceki_belge", "Önceki be&lge", "chevron-left", "Ctrl+Left", ctx="kontrol",
       menu="git"),
    _a("kontrol.sayfa", "Önceki / sonraki sayfa", None, ("Left", "Right"), ctx="kontrol",
       local=True, palette=False),
    _a("kontrol.ilk_son", "İlk / son sayfa", None, ("Home", "End"), ctx="kontrol",
       local=True, palette=False),
    _a("kontrol.ekran", "Bir ekran geri / ileri", None, ("PgUp", "PgDown"), ctx="kontrol",
       local=True, palette=False),
    _a("kontrol.secimi_genislet", "Seçimi genişlet", None, ("Shift+Left", "Shift+Right"),
       ctx="kontrol", local=True, palette=False),

    # Şablonlar
    _a("sablonlar.kutu_ciz", "Kutu çi&z", "scan", "B", ctx="sablonlar", menu="araclar",
       checkable=True, kw="alan çerçeve"),
    _a("sablonlar.izgara", "Izgaraya &oturt", "magnet", "G", ctx="sablonlar",
       menu="araclar", checkable=True, kw="hizala mıknatıs grid"),
    _a("sablonlar.dene", "&Bütün örneklerde dene", "play", "Ctrl+T", ctx="sablonlar",
       menu="araclar", kw="oku test"),
    _a("sablonlar.kutu_sil", "Kutuyu &sil", "trash-2", "Del", ctx="sablonlar",
       menu="duzen", tip="Kutuyu sil (geri alınabilir)"),
    _a("sablonlar.kutu_cogalt", "Kutuyu çoğa&lt", None, "Ctrl+D", ctx="sablonlar",
       menu="duzen", kw="kopyala"),
    _a("sablonlar.degisken_ekle", "Değişken &ekle", "plus", "Ctrl+Shift+N", ctx="sablonlar",
       menu="duzen", kw="alan"),
    _a("sablonlar.yukari", "Değişkeni yuka&rı taşı", "arrow-up", "Alt+Up", ctx="sablonlar",
       menu="duzen", kw="sırala"),
    _a("sablonlar.asagi", "Değişkeni &aşağı taşı", "arrow-down", "Alt+Down",
       ctx="sablonlar", menu="duzen", kw="sırala"),
    _a("sablonlar.okumalari_goster", "&Okumaları sayfada göster", "eye", ctx="sablonlar",
       menu="gorunum", checkable=True),
    _a("sablonlar.kaydir", "Kutuyu 0,25 mm kaydır", None, ("Left", "Up", "Right", "Down"),
       ctx="sablonlar", local=True, palette=False),
    _a("sablonlar.kaydir_1mm", "Kutuyu 1 mm kaydır", None,
       ("Shift+Left", "Shift+Up", "Shift+Right", "Shift+Down"), ctx="sablonlar",
       local=True, palette=False),
    _a("sablonlar.el", "Sayfayı sürükle (basılı tut)", "move", "Space", ctx="sablonlar",
       local=True, palette=False),

    # Değerler
    _a("degerler.onayla", "Onayl&a ve sonrakine geç", "check", ("Return", "Enter"),
       ctx="degerler", menu="duzen", tip="Öneriyi kabul et, incelendi işaretle ve geç",
       kw="kabul öneri"),
    _a("degerler.secilenleri_onayla", "&Seçilenleri onayla", "check-check",
       ("Ctrl+Return", "Ctrl+Enter"), ctx="degerler", menu="duzen", kw="kabul toplu"),
    _a("degerler.elle_yaz", "&Elle yaz", "pencil", "F2", ctx="degerler", menu="duzen",
       kw="düzenle değiştir"),
    _a("degerler.varyant", "Yeni &varyant çiz", "scan", "V", ctx="degerler", menu="duzen",
       kw="kutu"),
    _a("degerler.vazgec", "Va&zgeç", None, "Esc", ctx="degerler", menu="duzen",
       tip="Değişikliği bırak"),
    _a("degerler.tumunu_sec", "&Tümünü seç", "check-check", "Ctrl+A", ctx="degerler",
       menu="duzen"),
    _a("degerler.tum_sayfa", "Tüm sayfayı &göster", "file-text", "Space", ctx="degerler",
       menu="gorunum", kw="önizleme"),
    _a("degerler.sonraki_kontrol", "Sonraki kon&trol", "triangle-alert", "N",
       ctx="degerler", menu="git", kw="şüpheli uyarı"),
    _a("degerler.onceki_kontrol", "Önceki k&ontrol", "triangle-alert", "Shift+N",
       ctx="degerler", menu="git", kw="şüpheli uyarı"),
    _a("degerler.tumunu_incele", "&Tümünü incele", "list-checks", ctx="degerler",
       menu="araclar", checkable=True, tip="Emin olanlar dahil her değeri sırayla göster"),
    _a("degerler.ornek_kontrol", "Örnek kont&rol", "shuffle", ctx="degerler", menu="araclar",
       checkable=True, tip="Dışa aktarmadan önce rastgele 20 emin değere bak"),
    _a("degerler.oku", "Değerleri &oku", "scan-text", ctx="degerler", menu="araclar",
       tip="Şablonu olan bütün belgeleri yeniden oku", kw="ocr okuma"),
    _a("degerler.eksikleri_oku", "Yalnızca &eksikleri oku", "list-filter", ctx="degerler",
       menu="araclar", tip="Yalnızca eksikleri oku", kw="ocr okuma eksik"),
    _a("degerler.durdur", "Okumayı &durdur", "square", "Ctrl+.", ctx="degerler",
       menu="araclar", kw="iptal"),
    _a("degerler.sonraki_deger", "Sonraki / önceki değer", None, ("Tab", "Shift+Tab"),
       ctx="degerler", local=True, palette=False),

    # Dışa Aktar
    _a("disa_aktar.durdur", "Dışa aktarmayı &durdur", "square", "Ctrl+.", ctx="disa_aktar",
       menu="araclar", kw="iptal"),

    # Rehber
    _a("rehber.aramayi_temizle", "Aramayı temizle", "x", "Esc", ctx="rehber", local=True,
       palette=False),
)

MENU_LAYOUT: dict[str, tuple[str | None, ...]] = {
    "dosya": ("app.yeni_is", "app.dosya_ekle", SEPARATOR, "app.kaydet", "app.disa_aktar",
              "yukle.klasor_ekle", "disa_aktar.index_ac", "yukle.gezginde_goster",
              "disa_aktar.gezginde_goster", SEPARATOR,
              "rehber.yazdir", "rehber.pdf_ac", "disa_aktar.yazdir", SEPARATOR, "app.isi_kapat",
              "app.cikis"),
    "duzen": ("app.geri_al", "app.yinele", SEPARATOR, "kontrol.tumunu_sec",
              "kontrol.secimi_kaldir", "degerler.tumunu_sec", SEPARATOR,
              "kontrol.onayla", "kontrol.kes", "kontrol.birlestir", "kontrol.saga_dondur",
              "kontrol.sola_dondur", "kontrol.sil",
              "degerler.onayla", "degerler.secilenleri_onayla", "degerler.elle_yaz",
              "degerler.varyant", "degerler.vazgec",
              "sablonlar.degisken_ekle", "sablonlar.yukari", "sablonlar.asagi",
              "sablonlar.kutu_cogalt", "sablonlar.kutu_sil",
              "yukle.yeniden_adlandir", "yukle.yukari", "yukle.asagi", "yukle.cikar",
              SEPARATOR, "app.bul", "app.sonraki_sonuc", "app.onceki_sonuc"),
    "gorunum": ("app.yakinlastir", "app.uzaklastir", "app.sigdir", SEPARATOR,
                "kontrol.onizle", "degerler.tum_sayfa", "sablonlar.okumalari_goster",
                SEPARATOR, "app.yan_panel", "app.yazi_buyut", "app.yazi_kucult",
                "app.tam_ekran"),
    "git": (*(f"app.sekme.{tab}" for tab in TABS), "app.sonraki_sekme", "app.onceki_sekme",
            SEPARATOR, "app.git", SEPARATOR,
            "kontrol.sonraki_kontrol", "kontrol.onceki_kontrol",
            "kontrol.sonraki_incelenmemis", "kontrol.sonraki_belge", "kontrol.onceki_belge",
            "degerler.sonraki_kontrol", "degerler.onceki_kontrol"),
    "araclar": ("kontrol.filtre", "kontrol.sablon", "kontrol.degerlerde_ac",
                "sablonlar.kutu_ciz", "sablonlar.izgara", "sablonlar.dene",
                "degerler.oku", "degerler.eksikleri_oku", "degerler.tumunu_incele",
                "degerler.ornek_kontrol", "degerler.durdur",
                "yukle.iptal", "disa_aktar.durdur", SEPARATOR, "app.ayarlar"),
    "yardim": ("app.yardim", "app.kisayollar", "app.komut_ara", SEPARATOR, "app.hakkinda"),
}

_BY_ID = {spec.id: spec for spec in SPECS}


def plain_text(text: str) -> str:
    """Menu text without its & access key marker."""
    return text.replace("&&", "\0").replace("&", "").replace("\0", "&")


def access_key(text: str) -> str | None:
    """The letter after the single & in a menu text, upper-cased, or None."""
    i = text.replace("&&", "  ").find("&")
    return text[i + 1].upper() if 0 <= i < len(text) - 1 else None


def tooltip_for(spec: ActionSpec) -> str:
    """Tooltip text: the label (or spec tooltip) and its first shortcut, '… (Ctrl+N)'."""
    base = spec.tooltip or plain_text(spec.text).rstrip("…")
    return f"{base} ({key_text(spec.shortcuts[0])})" if spec.shortcuts else base


def fold(text: str) -> str:
    """Turkish-aware case folding for search: İ/i and I/ı fold together, accents dropped."""
    text = text.replace("İ", "i").replace("I", "ı").lower().replace("ı", "i")
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def spec(action_id: str) -> ActionSpec:
    return _BY_ID[action_id]


def _active(spec: ActionSpec, tab: str | None) -> bool:
    return spec.context == "app" or spec.context == tab


def _group(spec: ActionSpec) -> str:
    if spec.context != "app":
        return TABS[spec.context]
    return plain_text(MENUS[spec.menu]) if spec.menu else "Genel"


# Derived views
class SheetRow(NamedTuple):
    group: str
    text: str
    keys: list[str]


class PaletteEntry(NamedTuple):
    id: str
    text: str
    keys: list[str]
    enabled: bool
    keywords: str  # folded search text


def menu_structure(tab: str | None = None) -> list[tuple[str, list[str | None]]]:
    """The six menus in order: (title with &, action ids with None as separator).

    With `tab`, only "app" actions and that tab's actions are kept, and separators are tidied.
    """
    menus = []
    for key, title in MENUS.items():
        items: list[str | None] = []
        for item in MENU_LAYOUT[key]:
            if item is SEPARATOR:
                if items and items[-1] is not SEPARATOR:
                    items.append(SEPARATOR)
            elif tab is None or _active(_BY_ID[item], tab):
                items.append(item)
        while items and items[-1] is SEPARATOR:
            items.pop()
        menus.append((title, items))
    return menus


def shortcut_sheet(tab: str) -> list[SheetRow]:
    """Rows for the shortcut sheet (Shift+F1): every key that works on `tab`."""
    return [SheetRow(_group(s), plain_text(s.text).rstrip("…"), [key_text(k) for k in s.shortcuts])
            for s in SPECS if s.shortcuts and _active(s, tab)]


def search_text(spec: ActionSpec) -> str:
    return fold(" ".join((plain_text(spec.text), spec.tooltip, _group(spec), *spec.keywords)))


def palette_search(entries: list[PaletteEntry], query: str) -> list[PaletteEntry]:
    """Entries whose text or keywords contain every word of `query` (Turkish folding)."""
    words = fold(query).split()
    return [e for e in entries if all(w in e.keywords for w in words)]


# Validation
def validate(specs: tuple[ActionSpec, ...] = SPECS) -> list[str]:
    """Problems with the table, empty when it is sound."""
    errors: list[str] = []
    ids = [s.id for s in specs]
    errors += [f"{i}: id used twice" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for s in specs:
        if not plain_text(s.text).strip():
            errors.append(f"{s.id}: no text")
        if s.context not in CONTEXTS:
            errors.append(f"{s.id}: unknown context {s.context!r}")
        if s.menu is not None and s.menu not in MENUS:
            errors.append(f"{s.id}: unknown menu {s.menu!r}")
        for key in s.shortcuts:
            seq = key_sequence(key)
            portable = seq.toString(QKeySequence.SequenceFormat.PortableText)
            if seq.count() != 1:
                errors.append(f"{s.id}: {key!r} is not one key chord")
                continue
            mods, code = seq[0].keyboardModifiers(), seq[0].key().value
            if code == Qt.Key.Key_I.value or (code < 0x110000 and chr(code) in _TURKISH):
                errors.append(f"{s.id}: {portable} uses a Turkish-only letter or I")
            if (mods & Qt.KeyboardModifier.ControlModifier
                    and mods & Qt.KeyboardModifier.AltModifier):
                errors.append(f"{s.id}: {portable} is Ctrl+Alt (AltGr on Turkish Q)")
        typing = not s.local and any(is_typing_key(k) for k in s.shortcuts)
        if s.single_key != typing:
            errors.append(f"{s.id}: single_key should be {typing}")
    for tab in TABS:
        seen: dict[str, str] = {}
        for s in specs:
            if not _active(s, tab):
                continue
            for key in s.shortcuts:
                name = key_sequence(key).toString(QKeySequence.SequenceFormat.PortableText)
                if name in seen and seen[name] != s.id:
                    errors.append(f"{tab}: {name} used by {seen[name]} and {s.id}")
                seen[name] = s.id
    errors += _validate_menus(specs)
    return errors


def _validate_menus(specs: tuple[ActionSpec, ...]) -> list[str]:
    errors = []
    by_id = {s.id: s for s in specs}
    titles = [access_key(t) for t in MENUS.values()]
    if len(set(titles)) != len(titles):
        errors.append("menu bar: access keys repeat")
    placed = {item: key for key, items in MENU_LAYOUT.items() for item in items if item}
    for s in specs:
        if s.menu != placed.get(s.id):
            errors.append(f"{s.id}: menu is {s.menu!r} but the layout puts it in "
                          f"{placed.get(s.id)!r}")
    for item in placed:
        if item not in by_id:
            errors.append(f"menu layout: unknown action {item}")
    for tab in TABS:
        for title, items in menu_structure(tab):
            letters = []
            for item in filter(None, items):
                letter = access_key(by_id[item].text) if item in by_id else None
                if letter is None or not ("A" <= letter <= "Z") or letter == "I":
                    errors.append(f"{tab} {plain_text(title)}: {item} needs an ASCII access "
                                  "key other than I")
                letters.append(letter)
            for letter in {x for x in letters if letters.count(x) > 1}:
                errors.append(f"{tab} {plain_text(title)}: access key {letter} repeats")
    for title in MENUS.values():
        letter = access_key(title)
        if letter is None or not ("A" <= letter <= "Z") or letter == "I":
            errors.append(f"menu bar: {title} needs an ASCII access key other than I")
    return errors


# The registry
class Registry(QObject):
    """QActions for one window, built from SPECS.

    An action is enabled when a handler is connected, the screen has not disabled it, and it
    belongs to "app" or the current tab. Tab actions of other tabs are also hidden, so their
    keys are free for the current tab.
    """

    def __init__(self, window: QWidget, specs: tuple[ActionSpec, ...] = SPECS) -> None:
        super().__init__(window)
        self._specs = {s.id: s for s in specs}
        self._actions: dict[str, QAction] = {}
        self._connected: set[str] = set()
        self._disabled: set[str] = set()
        self._routes: dict[str, dict[str, Callable[..., object]]] = {}
        self._tab_disabled: set[tuple[str, str]] = set()
        self._context = next(iter(TABS))
        self._typing = False
        for s in specs:
            action = QAction(plain_text(s.text) if not s.menu else s.text, window)
            action.setObjectName(s.id)
            action.setToolTip(tooltip_for(s))
            action.setCheckable(s.checkable)
            action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
            action.setProperty("lucide", s.icon or "")
            window.addAction(action)
            self._actions[s.id] = action
        self._refresh()

    # Lookup
    def action(self, action_id: str) -> QAction:
        return self._actions[action_id]

    def spec(self, action_id: str) -> ActionSpec:
        return self._specs[action_id]

    @property
    def context(self) -> str:
        return self._context

    # State
    def connect(self, action_id: str, slot: Callable[..., object]) -> None:
        """Run `slot` when the action triggers (checkable actions pass the checked state)."""
        self._actions[action_id].triggered.connect(slot)
        self._connected.add(action_id)
        self._refresh(action_id)

    def set_enabled(self, action_id: str, enabled: bool) -> None:
        """Screen-level state, e.g. "nothing selected"; context still applies on top."""
        (self._disabled.discard if enabled else self._disabled.add)(action_id)
        self._refresh(action_id)

    def connect_tab(self, action_id: str, tab: str, slot: Callable[..., object]) -> None:
        """Route an app-wide action (Ctrl+F, F3, Ctrl+G...) to `slot` only while `tab` is
        current. Each tab has at most one route; a tab without one leaves the action disabled,
        so a key never silently does nothing and two tabs' slots never both fire."""
        if tab not in TABS:
            raise ValueError(f"unknown tab: {tab}")
        routes = self._routes.get(action_id)
        if routes is None:
            routes = self._routes[action_id] = {}
            self._actions[action_id].triggered.connect(partial(self._dispatch, action_id))
        routes[tab] = slot
        self._refresh(action_id)

    def set_enabled_for(self, action_id: str, tab: str, enabled: bool) -> None:
        """Per-tab state of a routed action (e.g. Rehber's F3 with no hits)."""
        key = (action_id, tab)
        (self._tab_disabled.discard if enabled else self._tab_disabled.add)(key)
        if tab == self._context:
            self._refresh(action_id)

    def routes(self, action_id: str) -> tuple[str, ...]:
        """The tabs that answer a routed action."""
        return tuple(self._routes.get(action_id, ()))

    def _dispatch(self, action_id: str, checked: bool = False) -> None:
        slot = self._routes.get(action_id, {}).get(self._context)
        if slot is None:
            return
        if self._specs[action_id].checkable:
            slot(checked)
        else:
            slot()

    def _handled(self, action_id: str, tab: str) -> bool:
        if action_id in self._connected:
            return True
        return tab in self._routes.get(action_id, {})

    def _usable(self, action_id: str, tab: str) -> bool:
        return (self._handled(action_id, tab) and action_id not in self._disabled
                and (action_id, tab) not in self._tab_disabled)

    def set_context(self, tab: str) -> None:
        """Make `tab` current: only "app" actions and this tab's actions stay active."""
        if tab not in TABS:
            raise ValueError(f"unknown tab: {tab}")
        self._context = tab
        self._refresh()

    def set_typing(self, typing: bool) -> None:
        """While a text field has focus, typing keys (letters, Enter, Del…) are unbound."""
        if typing != self._typing:
            self._typing = typing
            self._refresh()

    def is_enabled(self, action_id: str) -> bool:
        """Enabled for the user (ignores the typing guard, which only unbinds keys)."""
        return self._actions[action_id].isEnabled()

    def live_keys(self, action_id: str) -> list[str]:
        """The keys bound right now, PortableText."""
        return [k.toString(QKeySequence.SequenceFormat.PortableText)
                for k in self._actions[action_id].shortcuts()]

    def _refresh(self, only: str | None = None) -> None:
        for action_id in [only] if only else self._specs:
            s = self._specs[action_id]
            action = self._actions[action_id]
            active = _active(s, self._context)
            action.setVisible(active)
            action.setEnabled(active and self._usable(action_id, self._context))
            keys = [] if s.local else [key_sequence(k) for k in s.shortcuts]
            if self._typing and s.single_key:
                keys = [k for k in keys if not is_typing_key(k)]
            action.setShortcuts(keys)

    # Derived views with live state
    def palette_entries(self, tab: str | None = None) -> list[PaletteEntry]:
        """Every palette action of "app" and `tab` (default: the current tab)."""
        tab = tab or self._context
        return [PaletteEntry(s.id, plain_text(s.text), [key_text(k) for k in s.shortcuts],
                             self._usable(s.id, tab), search_text(s))
                for s in self._specs.values() if s.palette and _active(s, tab)]

    def install_text_guard(self, app: QApplication | None = None) -> TextFocusGuard:
        """Follow keyboard focus so typing keys never fire while a text field has focus."""
        return TextFocusGuard(self, app)


def is_text_input(widget: QWidget | None) -> bool:
    """True when `widget` takes typed text (line edit, text edit, spin box, editable combo)."""
    if isinstance(widget, QLineEdit):
        return not widget.isReadOnly()
    if isinstance(widget, QTextEdit | QPlainTextEdit):
        return not widget.isReadOnly()
    if isinstance(widget, QAbstractSpinBox):
        return not widget.isReadOnly()
    if isinstance(widget, QComboBox):
        return widget.isEditable()
    return False


class TextFocusGuard(QObject):
    """Unbinds typing keys of single-key actions while a text input has focus."""

    def __init__(self, registry: Registry, app: QApplication | None = None) -> None:
        super().__init__(registry)
        self._registry = registry
        app = app or QApplication.instance()
        app.focusChanged.connect(self._focus_changed)
        registry.set_typing(is_text_input(app.focusWidget()))

    def _focus_changed(self, _old: QWidget | None, new: QWidget | None) -> None:
        self._registry.set_typing(is_text_input(new))
