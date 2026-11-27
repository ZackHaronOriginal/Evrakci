"""Why a key cannot act (Q-09): one text per disabled command, never silent.

`reason(window, action_id, tab)` is the registry's reason source (`Registry.set_reason_source`).
While a command of the current tab is disabled it returns the sentence that says why; the
registry then shows it as the greyed menu item's and button's tooltip, in the palette, and in the
status bar when the command's key is pressed. The texts below are the ones the owner approved
(docs/ui-goal/shortcut-mismatches.md, "New Turkish texts"); where an old text already existed it
is reused, never reworded.
"""

from __future__ import annotations

from evrakci.ui.kontrol_actions import NO_JOB_TEXT
from evrakci.ui.workers import BUSY_REASON

GO_TO_ELSEWHERE = "Belgeye gitmek için Kontrol sekmesini açın (Ctrl+2)."
NO_DOCUMENT = "Gidilecek bir belge yok."
DOCUMENT_NOT_SHOWN = "Belge {number} bu görünümde yok."
PAGE_NOT_SHOWN = "Sayfa {number} bu görünümde yok."
READ_FAILED = "Örnek sayfa okunamadı. Yükle sekmesinden işi kontrol edin."
DAMAGED_NEXT = " Dosyayı kontrol edin veya silin."
NO_VARIABLE_TO_FIND = "Aranacak değişken yok."
NO_RESULTS_HERE = "Bu sekmede aranacak sonuç yok."
NO_HITS = "Sonuç yok."
NOTHING_TO_SAVE_HERE = "Rehber'de kaydedilecek bir şey yok."
NO_TEMPLATE_TO_SAVE = "Kaydedilecek bir şablon yok. Önce bir şablon oluşturun."
NOTHING_TO_UNDO = "Geri alınacak bir şey yok."
NOTHING_TO_REDO = "Yinelenecek bir şey yok."
REHBER_NOTHING_TO_UNDO = "Rehber'de geri alınacak bir şey yok."
REHBER_NOTHING_TO_REDO = "Rehber'de yinelenecek bir şey yok."
NO_ZOOM_HERE = "Bu sekmede yakınlaştırılacak bir şey yok."
NOTHING_TO_REFRESH = "Bu sekmede yenilenecek bir şey yok."
EXPORT_RUNNING = "Dışa aktarma sürerken yenilenemez."
BATCH_FIRST = "Parti zaten ilk sırada."
BATCH_LAST = "Parti zaten son sırada."
PICK_BATCH = "Önce bir parti seçin."
NOTHING_RUNNING = "Şu an durdurulacak bir iş yok."
PICK_TEMPLATE_FIRST = "Önce bir şablon seçin ya da oluşturun."
PICK_VARIABLE_OR_BOX = "Önce bir değişken ya da kutu seçin."
PICK_BOX = "Önce bir kutu seçin."
PICK_VARIABLE = "Önce bir değişken seçin."
ALREADY_FIRST = "Zaten ilk sırada."
ALREADY_LAST = "Zaten son sırada."
NO_PAGE_TO_DRAW = "Kutu çizmek için bir şablon ve bir örnek sayfa gerekir."
NO_PAGE_FOR_GRID = "Izgara için bir şablon ve bir örnek sayfa gerekir."
NO_PAGE_TO_TRY = "Denemek için bir şablon ve açık bir iş gerekir."
NO_PAGE_FOR_WEAK = "Zayıf örnekler için bir şablon ve bir örnek sayfa gerekir."
TRY_RUNNING = "Deneme sürüyor; bitince yeniden deneyin."
PICK_VALUE = "Önce bir değer seçin."
PICK_ROWS = "Önce satırları seçin."
NO_ROWS = "Seçilecek bir satır yok."
NO_COLUMNS = "Sıfırlanacak bir sütun yok."
PICK_TEMPLATE_DOCUMENT = "Önce şablonu olan bir belge seçin."
NO_CHECK_WAITING = "Kontrol bekleyen değer yok."
NO_FOLDER_TO_SHOW = "Gösterilecek bir klasör yok."
NO_INDEX_PAGE = "Yazdırılacak dizin sayfası yok."
NO_LIST_TO_COPY = "Kopyalanacak bir ad listesi yok."
NO_INDEX_FILE = "Henüz yazılmış bir dizin dosyası yok."
NO_NAMES_TO_COMPARE = "Karşılaştırılacak ad yok."
NO_CORRECTED_VALUE = "Düzeltilmiş bir değer yok."
TYPED_BY_HAND = "Bu değer elle yazıldı; okunmuş bir değer yok."
NO_PAGE_FOR_READS = "Okumaları göstermek için bir şablon ve bir örnek sayfa gerekir."
READ_FIRST = "Önce değerleri okuyun."
NOTHING_TO_READ = "Okunacak, şablonu olan bir belge yok."
READ_RUNNING = "Okuma sürüyor."
READING_NOW = "Okuma sürerken geri alınamaz."

_ZOOM = ("app.yakinlastir", "app.uzaklastir", "app.sigdir")
_WEAK = ("sablonlar.sonraki_zayif", "sablonlar.onceki_zayif", "sablonlar.zayif_ornekler")


def _no_job(window) -> bool:
    return window.controller() is None


def reason(window, action_id: str, tab: str) -> str | None:
    """The sentence that says why `action_id` cannot act on `tab` now, or None."""
    fn = _RULES.get(action_id)
    if fn is not None:
        return fn(window, tab)
    if action_id.startswith("kontrol."):
        return NO_JOB_TEXT if _no_job(window) else None
    return None


# -- app ---------------------------------------------------------------------------------------
def _git(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else None


def _save(window, tab: str) -> str | None:
    if tab == "rehber":
        return NOTHING_TO_SAVE_HERE
    if tab == "sablonlar":
        return NO_TEMPLATE_TO_SAVE
    return NO_JOB_TEXT


def _export(window, tab: str) -> str | None:
    if window.loading():
        return BUSY_REASON
    if _no_job(window):
        return NO_JOB_TEXT
    screen = window.disa_aktar
    if screen._state == "running":
        return "Dışa aktarma sürüyor."
    blocked = [f for f in screen._findings if f.level == "engel" and f.title]
    return "Dışa aktarılamıyor: " + blocked[0].title if blocked else None


def _close(window, tab: str) -> str | None:
    return NO_JOB_TEXT


def _loading_new(window, tab: str) -> str | None:
    return BUSY_REASON


def _undo(window, tab: str) -> str | None:
    if tab == "rehber":  # it shows nothing of the job, so it never undoes it unseen (B-055)
        return REHBER_NOTHING_TO_UNDO
    if window.degerler.busy():
        return READING_NOW
    return NOTHING_TO_UNDO


def _redo(window, tab: str) -> str | None:
    if tab == "rehber":
        return REHBER_NOTHING_TO_REDO
    if window.degerler.busy():
        return READING_NOW
    return NOTHING_TO_REDO


def _find(window, tab: str) -> str | None:
    if tab == "sablonlar":
        return NO_VARIABLE_TO_FIND
    return NO_JOB_TEXT


def _hit(window, tab: str) -> str | None:
    return NO_HITS if tab == "rehber" else NO_RESULTS_HERE


def _zoom(window, tab: str) -> str | None:
    return NO_ZOOM_HERE


def _refresh(window, tab: str) -> str | None:
    if tab == "disa_aktar":
        return NO_JOB_TEXT if _no_job(window) else EXPORT_RUNNING
    return NOTHING_TO_REFRESH


def _panel(window, tab: str) -> str | None:
    return NO_JOB_TEXT


# -- Yükle -------------------------------------------------------------------------------------
def _yukle_position(window) -> tuple[int, int]:
    screen = window.yukle
    controller = screen.controller
    ids = [b.id for b in controller.job.batches] if controller is not None else []
    batch_id = screen.table.selected_batch()
    return (ids.index(batch_id) if batch_id in ids else -1), len(ids)


def _yukle_up(window, tab: str) -> str | None:
    if _no_job(window):
        return NO_JOB_TEXT
    pos, _count = _yukle_position(window)
    return PICK_BATCH if pos < 0 else BATCH_FIRST


def _yukle_down(window, tab: str) -> str | None:
    if _no_job(window):
        return NO_JOB_TEXT
    pos, _count = _yukle_position(window)
    return PICK_BATCH if pos < 0 else BATCH_LAST


def _yukle_remove(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else PICK_BATCH


def _yukle_open(window, tab: str) -> str | None:
    """Partiyi Kontrol'de aç: needs a job, a chosen batch and no read running."""
    if _no_job(window):
        return NO_JOB_TEXT
    return "Okuma bitince açılır." if window.yukle.busy() else PICK_BATCH


def _needs_job(window, tab: str) -> str | None:
    return NO_JOB_TEXT


def _stop(window, tab: str) -> str | None:
    return NOTHING_RUNNING


# -- Şablonlar ---------------------------------------------------------------------------------
def _sablon_page(window) -> bool:
    screen = window.sablon
    return screen.template is not None and screen.canvas.has_page()


def _draw(window, tab: str) -> str | None:
    return NO_PAGE_TO_DRAW


def _grid(window, tab: str) -> str | None:
    return NO_PAGE_FOR_GRID


def _try(window, tab: str) -> str | None:
    if window.loading():
        return BUSY_REASON
    screen = window.sablon
    if _sablon_page(window) and screen._all_task is not None:
        return TRY_RUNNING
    return NO_PAGE_TO_TRY


def _weak(window, tab: str) -> str | None:
    return NO_PAGE_FOR_WEAK


def _box_delete(window, tab: str) -> str | None:
    return PICK_VARIABLE_OR_BOX


def _box_copy(window, tab: str) -> str | None:
    screen = window.sablon
    return PICK_TEMPLATE_FIRST if screen.template is None else PICK_BOX


def _add_variable(window, tab: str) -> str | None:
    return PICK_TEMPLATE_FIRST


def _move(window, tab: str, step: int) -> str | None:
    screen = window.sablon
    if screen.template is None:
        return PICK_TEMPLATE_FIRST
    variable = screen.current_variable()
    if variable is None:
        return PICK_VARIABLE
    return ALREADY_FIRST if step < 0 else ALREADY_LAST


def _sablon_up(window, tab: str) -> str | None:
    return _move(window, tab, -1)


def _sablon_down(window, tab: str) -> str | None:
    return _move(window, tab, 1)


# -- Değerler ----------------------------------------------------------------------------------
def _degerler_value(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else PICK_VALUE


def _degerler_rows(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else PICK_ROWS


def _degerler_select_all(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else NO_ROWS


def _degerler_template(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else PICK_TEMPLATE_DOCUMENT


def _degerler_revert(window, tab: str) -> str | None:
    if _no_job(window):
        return NO_JOB_TEXT
    screen = window.degerler
    cell = screen._cell_for(screen.table.currentIndex())
    if cell is not None and cell.value is not None and cell.value.edited:
        return TYPED_BY_HAND
    return NO_CORRECTED_VALUE


def _degerler_columns(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else NO_COLUMNS


def _degerler_escape(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else NO_DOCUMENT


def _degerler_check(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else NO_CHECK_WAITING


def _read(window, tab: str) -> str | None:
    if _no_job(window):
        return NO_JOB_TEXT
    if window.loading():
        return BUSY_REASON
    if window.degerler.task is not None:
        return READ_RUNNING
    return NOTHING_TO_READ


def _read_missing(window, tab: str) -> str | None:
    reason = _read(window, tab)
    return READ_FIRST if reason == NOTHING_TO_READ and window.degerler.rows else reason


def _review_mode(window, tab: str) -> str | None:
    return NO_JOB_TEXT if _no_job(window) else READ_FIRST


def _show_reads(window, tab: str) -> str | None:
    return NO_PAGE_FOR_READS


# -- Dışa Aktar --------------------------------------------------------------------------------
def _print_index(window, tab: str) -> str | None:
    return NO_INDEX_PAGE


def _show_folder(window, tab: str) -> str | None:
    return NO_FOLDER_TO_SHOW


def _copy_list(window, tab: str) -> str | None:
    return NO_LIST_TO_COPY


def _open_index(window, tab: str) -> str | None:
    return NO_INDEX_FILE


def _compare(window, tab: str) -> str | None:
    return NO_NAMES_TO_COMPARE


_RULES = {
    "app.git": _git,
    "app.kaydet": _save,
    "app.disa_aktar": _export,
    "app.isi_kapat": _close,
    "app.yeni_is": _loading_new,
    "app.dosya_ekle": _loading_new,
    "app.geri_al": _undo,
    "app.yinele": _redo,
    "app.bul": _find,
    "app.sonraki_sonuc": _hit,
    "app.onceki_sonuc": _hit,
    "app.yenile": _refresh,
    "app.yan_panel": _panel,
    "yukle.yukari": _yukle_up,
    "yukle.asagi": _yukle_down,
    "yukle.cikar": _yukle_remove,
    "yukle.kontrolde_ac": _yukle_open,
    "yukle.yeniden_adlandir": _needs_job,
    "yukle.gezginde_goster": _needs_job,
    "yukle.iptal": _stop,
    "sablonlar.kutu_ciz": _draw,
    "sablonlar.izgara": _grid,
    "sablonlar.dene": _try,
    "sablonlar.kutu_sil": _box_delete,
    "sablonlar.kutu_cogalt": _box_copy,
    "sablonlar.degisken_ekle": _add_variable,
    "sablonlar.yukari": _sablon_up,
    "sablonlar.asagi": _sablon_down,
    **dict.fromkeys(("sablonlar.sablon_adlandir", "sablonlar.sablon_cogalt",
                     "sablonlar.sablon_sil", "sablonlar.sablon_disa"), _add_variable),
    "degerler.onayla": _degerler_value,
    "degerler.okunanla_onayla": _degerler_value,
    "degerler.elle_yaz": _degerler_value,
    "degerler.tum_sayfa": _degerler_value,
    "degerler.okunana_don": _degerler_revert,
    "degerler.secilenleri_onayla": _degerler_rows,
    "degerler.varyant": _degerler_template,
    "degerler.tumunu_sec": _degerler_select_all,
    "degerler.kontrolde_ac": _degerler_value,
    "degerler.vazgec": _degerler_escape,
    "degerler.sutunlari_sifirla": _degerler_columns,
    "degerler.sonraki_kontrol": _degerler_check,
    "degerler.onceki_kontrol": _degerler_check,
    "degerler.durdur": _stop,
    "degerler.oku": _read,
    "degerler.eksikleri_oku": _read_missing,
    "degerler.tumunu_incele": _review_mode,
    "degerler.ornek_kontrol": _review_mode,
    "sablonlar.okumalari_goster": _show_reads,
    "disa_aktar.durdur": _stop,
    "disa_aktar.yazdir": _print_index,
    "disa_aktar.gezginde_goster": _show_folder,
    "disa_aktar.liste_kopyala": _copy_list,
    "disa_aktar.index_ac": _open_index,
    "disa_aktar.adlari_karsilastir": _compare,
    **dict.fromkeys(_ZOOM, _zoom),
    **dict.fromkeys(_WEAK, _weak),
}
