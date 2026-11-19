# Owner queue

Questions and checks for the owner. The run keeps working on anything that does not depend on
them. One row each; never delete a row, set Status instead.

Kind: **blocking** (the named work waits for the answer) or **check** (the run continues; the owner
tries it on their PC and reports).

| ID | Phase | Kind | Question or check | Options / how to check | Blocks | Status |
|---|---|---|---|---|---|---|
| Q-01 | 0 | blocking | B-005 (S1): Ayarlar > Saklama says "Dışa aktarılan iş bu bilgisayarda ne kadar saklansın." but a day limit deletes every job unchanged for that many days, also jobs never exported (README documents this behaviour, the window label does not). Which way? | **a** keep the behaviour, change the label to e.g. "Son değişikliğinden bu kadar gün sonra iş silinir; dışa aktarılmamış olsa da." (your wording); **b** change the behaviour (window and CLI): the day limit deletes only jobs that were exported, the label stays; **c** both: the label above and also skip never-exported jobs | Phase 0 exit (no S1 open); B-005 fix | open |
| Q-02 | 1 | blocking | Apple HIG vs our approved decisions: 20 rows in `docs/ui-goal/rules-conflicts.md` (13 where our value differs, 7 where a choice is needed, e.g. inactive selection colour, toast auto-dismiss, menu order). Until you answer, our approved value applies and nothing changes in the look. | Per row: keep ours (default) / take HIG / the option named in the row | Changes to the look from these rows (Phase 4); nothing else waits | open |
| Q-03 | 1 | blocking | Which rules in `docs/ui-goal/rules.json` fail the build (enforced) and which are only reported? All 103 are "reported" now. Proposal: enforce the measured, verified ones that pass today or are cheap to fix: font floor 13 px (DEC-TYP), contrast tiers (D10), accessible names (AUD-A11Y-01), focus ring (D11), hit targets 24/28/32 (AUD-HIT); report spacing grid, radii and HIG layout rows. | yes to the proposal / your own list | CI gate in Phase 6 and the "zero failing enforced rules" check in Phase 4 | open |
