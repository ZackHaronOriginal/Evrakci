# Değerler audit: proposals for the owner

Nothing here is changed in `src`. Each item adds Turkish text, changes how A looks or behaves, or needs a decision.
Evidence ids are rows of `degerler-findings.md`.

## P-degerler-01 (F-degerler-46, rated S3 by the audit; the run lead rates it): Enter stores the Öneri, the cell shows the Okunan value

Measured (tests `test_f46_enter_stores_the_suggestion_while_the_cell_shows_the_reading` and `test_f46_the_accept_button_stores_the_suggestion_while_the_cell_shows_the_reading`, tests/ui/test_degerler.py): for a Kontrol value the cell's display text is `482I3` (the Okunan reading); pressing Enter in the table, and the "Onayla ve sonrakine geç" button, both store `48213` (the Öneri) and mark it İncelendi. The Öneri is visible only in the inspector (larger than Okunan) and in a hover tooltip. So the stored value differs from what the cell showed. The two tests assert the current behaviour as evidence; if the owner changes the semantics they must be rewritten with it. Not changed here (owner decision).

Decided and built (owner Q-12, 2026-11-26; B-056): the cell shows the Öneri with the Okunan smaller beside it; Enter stores the Öneri, Shift+Enter the Okunan; the two tests named above were rewritten as test_f46_* for the new behaviour.

Options:
1. Show the Öneri in the cell for Kontrol values (struck Okunan then Öneri, or "482I3 → 48213"): what is shown is what Enter stores. Changes A's cell look and adds a glyph, maybe text.
2. Enter confirms what the cell shows (Okunan); a separate key or button takes the Öneri ("Öneriyi kabul et"). Changes the Enter flow and the key contract.
3. Keep Enter, but ask or say first: the key hint under the table or the toast reads "Enter: 48213 (Öneri)"; first Enter on a Kontrol value only selects the Öneri, a second stores it. New text and one more press per value.

## P-degerler-02 (F-degerler-05): a read with failed documents reports success
Measured P-159..P-161: toast "12 belge okundu." with 10 documents failed. Needs new text (count the failures in the toast, show the failure sentence instead of "henüz okunmadı"); not done because no existing string covers it.

## P-degerler-03 (F-degerler-04): empty text accepted as a value
Needs the owner's decision whether an empty value may be confirmed on purpose; the fix would be in `_apply_edit` (ui) but changes behaviour.
