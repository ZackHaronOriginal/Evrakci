# Findings: value editing (Değerler)

Research for ideas only (5c). Nothing here is a decision. Written 2026-11-19. Our side: `inventory-degerler.md` (V-), `inventory-sablonlar.md` (S-17, S-16) and code at HEAD ab7a87d. External facts are paraphrased with the page that was opened.

## What we do today

- Enter on a flagged value with a suggestion takes the suggestion and moves on; F2 edits in place, starting from the suggestion; Enter stores, Esc drops (V-57, V-59, V-60).
- Any text, including empty, is accepted; nothing checks format or type (V-61, O-11). "Zorunlu" only matters at export (S-16, V-96); the table and inspector never show it (O-12).
- Typed, accepted and confirmed values are one state, İncelendi (V-33, V-34); the only way back is undo, the core has `revert_value` but only the CLI uses it (V-65, O-10, O-21).
- Every edit is one undo step and saved at once (V-64). Corrections survive a re-read (V-10).

## Table

| Practice | Who does it (opened page) | What we do (ID) | Gap | Cost | Perf cost | Risk |
|---|---|---|---|---|---|---|
| Enter confirms, a separate key postpones, keys move between processed fields | ABBYY FlexiCapture: Enter, Ctrl+Enter, Ctrl+Up/Down; Insert switches paste and replace mode in the field ([ABBYY docs](https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work)) | Enter, F2, Esc, Tab / Shift+Tab, N / Shift+N (V-50, V-51, V-57, V-60) | Movement parity. Going back to a value already confirmed is Shift+Tab only | S | none | none |
| A field with a validation pattern turns red when it fails, and approval is blocked until fixed | Transact Validate: red when not found, below the OCR confidence, or pattern not met ([Transact docs](https://ephesoft.com/docs/?p=47801)) | No validation (V-61) | A typed "12O4" in a number-like variable passes silently | M (needs a pattern or kind on the variable) | none | The product says the app assumes nothing about documents; any check must be optional |
| Typed formats for dates and numbers, regional settings by default | DocuWare: date-only or date-time, number format; default from the computer's regional settings ([DocuWare](https://knowledgecenter.docuware.com/docs/processing-documents)); invoice2data: decimal separator option, date formats, integer and float coercion, errors on a malformed number ([source of extract](https://github.com/invoice-x/invoice2data/blob/master/src/invoice2data/extract/invoice_template.py)) | Display type guessed from the read values only (V-18, O-17) | Turkish dates and decimal comma are not checked; the column look can change after a re-read | M | none | Locale bugs; user-decided types conflict with "assumes nothing" unless optional |
| Required fields are enforced and reported as a set | invoice2data: template can list required fields; when one is missing an error lists required and present fields and no partial output is returned ([source](https://github.com/invoice-x/invoice2data/blob/master/src/invoice2data/extract/invoice_template.py)). DocuWare: default value or abort when a value is missing ([DocuWare](https://knowledgecenter.docuware.com/docs/processing-documents)) | Zorunlu decides file name at export (S-16, V-96); not shown in Değerler (O-12); empty value accepted (O-11) | Cheapest check with real effect: block an empty confirm on a required variable and show a "zorunlu" mark | S | none | Blocking Enter annoys; use a visible mark and a message first |
| Fix known misreads with rules (1 vs I, 0 vs O, replacement lists) | DocuWare ([page](https://knowledgecenter.docuware.com/docs/processing-documents)); invoice2data `replace` pairs ([README](https://github.com/invoice-x/invoice2data)) | None; fixed by hand each time (V-59) | Repetitive correction of the same misread | M (rules live in the template) | none | Rule changes a correct value; must be visible |
| Correct one value, then apply the same fix to similar values | Our own sample check marks other unreviewed values of the template after an error (V-69) | Only inside Örnek | No "apply this fix to the other documents" for a systematic misread | M | M for a re-scan of rows | Silent mass edit; needs preview and one undo step |
| Return a corrected value to the machine reading | Our core `revert_value` and CLI `--geri-al` (V-65, O-21) | Window has only Ctrl+Z | Undo order is global; one wrong value cannot be reverted without undoing newer edits | S | none | none |
| Show how the final value differs from the read value | Our value card marks changed characters between read and suggestion (V-74) | After accepting, the machine reading is not visible (O-10) | Reviewer cannot audit "what did I change" | S | none | none |
| Confirm many at once | Transact approves a document with Validate and moves on ([Transact docs](https://ephesoft.com/docs/?p=47801)) | "Seçilenleri onayla" skips Okunamadı (V-58) | Parity | none | none | Mass approve of wrong values; the automation-bias study ([PMC5356416](https://pmc.ncbi.nlm.nih.gov/articles/PMC5356416)) found wrong advice raised commission errors by 56.9 % in a simulated task (students, so only a pointer) |
| Edit-mode cursor behaviour | ABBYY's Insert key toggles paste and replace modes ([ABBYY docs](https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work)) | Line editor with suggestion preselected (V-59) | Only matters for fix-one-character edits of long codes; ours starts with the suggestion, unmeasured whether a replace mode helps | S | none | Surprises users who press Insert by accident |

## Ideas for the owner's ranking

1. **Show "Zorunlu" in Değerler and warn on an empty required value.** Problem: empty accepted silently, file name fails at export (O-11, O-12). Who gains: staff who find out only at export. Evidence: [invoice2data source](https://github.com/invoice-x/invoice2data/blob/master/src/invoice2data/extract/invoice_template.py) (required fields reported as a set), [DocuWare](https://knowledgecenter.docuware.com/docs/processing-documents). Effort: S.
2. **"Okunana dön" (revert to machine reading) in the window.** Problem: V-65, O-10. Evidence: internal (core exists); ABBYY lets users revisit processed fields ([docs](https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work)). Effort: S.
3. **Optional value format per variable** (date, number, free text) with a red mark when typed or read text does not fit. Evidence: [Transact docs](https://ephesoft.com/docs/?p=47801), [DocuWare](https://knowledgecenter.docuware.com/docs/processing-documents). Effort: M. Must stay optional.
4. **Per-variable replace list.** Evidence: [DocuWare](https://knowledgecenter.docuware.com/docs/processing-documents), [invoice2data README](https://github.com/invoice-x/invoice2data). Effort: M.
5. **"Apply to similar" after a correction** with preview. Evidence: internal (V-69 does a version in Örnek). Effort: M.
6. **Make the display kind explicit instead of guessed** (O-17). Evidence: [DocuWare](https://knowledgecenter.docuware.com/docs/processing-documents) (declared formats). Effort: S to M.

## Unverified

- ABBYY does not say how uncertain characters are shown ([ABBYY docs](https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work)); our character marks (V-22) cannot be compared.
- invoice2data type declaration beyond the legacy name rules and the readthedocs site were not read (the readthedocs URL I tried returned 404).
- DocuWare page says nothing about a user verification step; whether DocuWare has one elsewhere is unknown.
- Whether typing speed or error rate changes with an Insert/replace mode: no study found.
- Whether the Değerler status "all reviewed" gates export: not checked in code.
