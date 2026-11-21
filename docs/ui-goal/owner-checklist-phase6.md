# Owner checklist, Phase 6

Four checks only you can do. Nothing here needs you to send a document, a screenshot of a
document or a file name: send back the summary text and the ledger rows, nothing else.
Real scans never go into the repository, the chat or any upload.

## 1. Real scans: window and command line must agree (step 2)

What you need: an **anonymised** copy of about 800 pages of scans (a few PDFs in one folder, in
scan order), a Python environment with Evrakçı installed (`pip install -e ".[dev]"` from the
repository, or the installed app's Python), and optionally `pip install psutil` (gives a real
peak-memory number per stage; without it the numbers are the process high-water mark so far).

1. Pick an empty output folder on a disk with room for about three times the scans' size
   (the tool writes the window's export, the command line's export, and a temporary working copy
   of the job, which it deletes at the end). It writes nowhere else and never uploads anything.
2. Optional, to also check value reading: create a template in the window or with
   `evrakci sablon ...` and note its id (`evrakci sablon listele`).
3. Run it, once for the normal case (both OCR modes, one after the other):

   ```bash
   python tools/real_scan_check.py C:\anonim-taramalar --cikti C:\kontrol-sonuc
   ```

   With a template: add `--sablon ID` (and `--sablon-kok KLASOR` if the templates are not in the
   default folder). If the scans have no QR separator pages, add `--her-n N` (every N pages is a
   document). OCR on 800 pages takes a long time (hours is possible); `--ocr kapali` runs only
   the no-OCR export, `--ocr acik` only the OCR one.
4. It prints a summary and writes the same text to `ozet.txt` in the output folder. It checks,
   for the window's export function and `evrakci is disa-aktar` on the same job: same file
   names, same page count per file, same cells in `index.xlsx`. Exit code 0 means every check
   passed.
5. **Send back only the summary text** (the lines from `REAL SCAN CHECK SUMMARY` to `RESULT`).
   It holds page counts, seconds, memory, PASS/FAIL lines and, on a FAIL, the first differing
   file names or row numbers. If a FAIL line shows a file name you consider private, replace the
   name with `X` before sending.
6. Then open the same job in the window by hand and note anything odd while you add, read, check,
   fix values and export (thumbnails late or missing, freezes, wrong values). Each problem is a
   ledger row (section 4).

Pass bar: `RESULT: PASS`; the window's export and the command line's export agree; stage times and
memory are the numbers you can live with (write them in the report; there is no fixed limit).

## 2. Windows installer on a clean user account (step 3)

1. In the latest green run of the "Windows installer" workflow, download the artifact
   **Evrakci-Kurulum** (the `.exe`). Optionally compare with the checksum if one is attached.
2. Create a new Windows user (Settings > Accounts > Other users), sign in as that user. Nothing
   of Evrakçı, Python or Tesseract may be installed for it.
3. **Install.** Run the `.exe`. Windows SmartScreen says "Windows protected your PC" and the
   publisher is "Unknown publisher". This is expected: the installer is not code-signed (signing
   is your decision, see `OWNER-QUEUE.md`). Choose More info > Run anyway. Finish the wizard.
   Check: Start menu entry exists, `evrakci --version` works in a new terminal, the window opens.
4. **Run.** Open the window, create a job from a synthetic PDF, read, export to an empty folder.
   Open one exported PDF and search for a word (the text layer must work).
5. **Upgrade.** Uninstall nothing. On a second clean account (or after step 6 and a reinstall),
   first install the old release 0.0.1 or 0.0.2 (from its GitHub Release), create a job, then run
   the new installer over it. Check: one entry in "Apps", the old job is still listed, the
   command is on PATH once (not twice), the window opens.
6. **Uninstall.** Settings > Apps > Evrakçı > Uninstall. Check: the program folder is gone,
   `evrakci` is no longer on PATH, and the job folder (`%LOCALAPPDATA%\Evrakci`) is still there
   (jobs are kept on purpose).
7. Write down: Windows version, which step failed (if any), the exact text of any message.

CI already runs the silent install, upgrade in place and uninstall on a Windows runner
(`.github/workflows/windows-installer.yml`, step "Install, upgrade and uninstall for the current
user"). Your run adds what CI cannot: SmartScreen, a really clean account, the window by hand,
and 0.0.1/0.0.2 as the old version.

## 3. Linux tarball (step 4)

Nothing to do unless you want to. It is automated: `.github/workflows/linux-build.yml`, job
`clean-system`, installs the tarball with `kur.sh` on clean `debian:12` and `ubuntu:24.04`
containers with only the packages the README lists, opens the window on a real X display and
uninstalls. The built tarball and its checksum are in the artifact **Evrakci-Linux** of the same
workflow run. Check that the latest run on the release commit is green.

## 4. How to report problems

Every problem becomes one row in `docs/ui-goal/bugs.md` (the ledger), newest last, next free ID
(B-0NN). Columns: ID, severity, tab, where (theme / size / text), repro, expected vs actual,
evidence, status `open`. Severity: S1 data loss, silent wrong output or no keyboard path; S2
unusable in a supported theme or size; S3 visible but workable; S4 polish. A difference found by
`real_scan_check.py` is S1 until explained.

You can also just describe the problem in one or two sentences with the step number from this
list and the summary text; the run adds the row. Do not attach real documents or screenshots of
them.
