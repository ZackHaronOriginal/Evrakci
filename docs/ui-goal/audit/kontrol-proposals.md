# Kontrol audit: proposals for the owner

Nothing here is changed in `src`. Each item changes how A behaves or looks, or adds text.

## P-kontrol-01 (F-kontrol-08, ledger B-033, S2): R and Del with the loupe open act on all selected pages

Measured: selected pages 1-3, loupe open on page 2, R rotates pages 1, 2 and 3 (`rotated ids=['b1/0','b1/1','b1/2']`, P-097).
The loupe shows one page and says nothing about the other two. Cause: `ui/kontrol.py:selected_rows (L242-L246)` has no loupe
branch; the loupe forwards the window shortcuts.

Options:
1. While the loupe is open, R / Del / T act on the shown page only (no new text; the loupe already shows which page).
   Risk: a user who selected 3 pages and peeked at one expects the 3 to be rotated.
2. Keep the behaviour and show "3 sayfa seçili" in the loupe head (new Turkish text, adds an element to A's loupe head).
3. Both: act on the shown page when the selection has more than one page and the loupe is open, and show nothing new.

Recommendation: option 1. It needs only the owner's yes on the behaviour.

## P-kontrol-02 (F-kontrol-06, S3, not fixed): newest toast waits behind older ones

Not done: the fix lives in the shared `ui/feedback.py:Toaster` and two existing tests assert the queue
(`test_feedback.py::test_toast_shows_one_and_queues`, `test_ledger_a.py` B-023 pair), so changing it changes every screen.
Options: (a) replace the visible toast when a newer one arrives (the history keeps the older step); (b) cap the queue at one.
Needs the owner's yes because both tests would change meaning.

## Note on F-kontrol-28

The restore branch of `kontrol.py:toggle_delete` already shows a toast ("N sayfa geri getirildi", L373-L374) at this HEAD,
so the row looks already fixed; the run lead should re-check it.
