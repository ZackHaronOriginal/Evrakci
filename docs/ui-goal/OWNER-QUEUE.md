# Owner queue

Questions and checks for the owner. The run keeps working on anything that does not depend on
them. One row each; never delete a row, set Status instead.

Kind: **blocking** (the named work waits for the answer) or **check** (the run continues; the owner
tries it on their PC and reports).

| ID | Phase | Kind | Question or check | Options / how to check | Blocks | Status |
|---|---|---|---|---|---|---|
| Q-01 | 0 | blocking | B-005 (S1): Ayarlar > Saklama says "Dışa aktarılan iş bu bilgisayarda ne kadar saklansın." but a day limit deletes every job unchanged for that many days, also jobs never exported (README documents this behaviour, the window label does not). Which way? | **a** keep the behaviour, change the label to e.g. "Son değişikliğinden bu kadar gün sonra iş silinir; dışa aktarılmamış olsa da." (your wording); **b** change the behaviour (window and CLI): the day limit deletes only jobs that were exported, the label stays; **c** both: the label above and also skip never-exported jobs | Phase 0 exit (no S1 open); B-005 fix | open |
