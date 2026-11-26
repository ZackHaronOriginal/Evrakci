# SignPath free OSS code signing: readiness checklist

Checked 2026-11-26 against the repo at /home/user/Evrakci. Research and checklist only; nothing here is applied.

## Sources

| Source | Result |
|---|---|
| https://signpath.org/terms | Opened. The requirement list below comes from it. |
| https://signpath.org | Opened. Says OSS is free and that SignPath verifies the binary was built from the open source repository. It lists no requirements. |
| https://signpath.org/apply | Fetched with curl. Only a cookie banner and the apply form heading were readable. No criteria text. |
| https://about.signpath.io/product/open-source | Opened with curl (the WebFetch call returned 502). Marketing page only. It mentions CI/CD connectors for GitHub and no eligibility rules. |
| https://signpath.io/open-source | 404. Not readable. |
| https://signpath.org/privacy-policy | 404 (a guessed link, not required). |

Not verified from any opened page: the SignPath GitHub Action name and inputs, the SignPath GitHub App (trusted build system) setup, the "tagged releases only" idea, and the exact wording an approved Code signing policy page needs. The SignPath Foundation docs (docs.signpath.io) were not fetched. Treat those rows as "to confirm at apply time".

## Requirements from https://signpath.org/terms, and the repo status

| # | Requirement (source: signpath.org/terms) | Status | Evidence in the repo |
|---|---|---|---|
| 1 | No malware or PUPs | Met (assumed) | Nothing suggests otherwise. SignPath checks this itself. |
| 2 | OSI-approved licence for all components, "without commercial dual-licensing for all components" | **Missing / blocking** | LICENSE is AGPL-3.0 (OSI approved). But docs/licensing.md and CONTRIBUTING.md and CLA.md state a commercial-licence model: the CLA lets the maintainer sublicense under "proprietary and commercial licenses", and licensing.md lists "Commercial licenses for organizations that cannot accept the AGPL". That is dual-licensing. |
| 3 | "No proprietary, non open-source component" | **Missing / blocking** | docs/licensing.md plans "Closed Pro modules". Nothing proprietary is in the repo today, but the stated plan conflicts. Bundled third-party components (Tesseract, Qt) are open source; docs/dependency-licenses.md lists them. |
| 4 | Actively maintained | Met | Recent commits, 2400-test suite, CI. |
| 5 | Already released in the form to be signed | Partly | Installer is built (windows-installer.yml, packaging/evrakci.iss) but `git tag` shows 0 tags and no GitHub release was checked (the API was blocked here). Needs a released v-tag installer. |
| 6 | Functionality described on a download page or store entry | Partly | README describes it and the install steps. No separate project website or download page. |
| 7 | Own project, own binaries only; same team signs and develops | Met | Single repo, own source. |
| 8 | No security-exploit or hacking features | Met | Document processing app. |
| 9 | Product name and version metadata set and enforced on binaries | Partly | packaging/freeze_setup.py sets version from `evrakci.__version__`; the .iss has AppPublisher and AppVersion. Company/product metadata on the .exe was not confirmed. Check with a version-info dump of the built exe. |
| 10 | Privacy: software that sends data to unspecified systems needs a privacy policy, shown at install, with a way to disable | **Missing** | No privacy statement anywhere. Network calls found in src: `urllib.request.urlopen` in src/evrakci/pipeline/ocr/models.py:82 (OCR model download, URL and SHA-256 from the rapidocr package) and src/evrakci/cli/ocr.py:282 (tur.traineddata from raw.githubusercontent.com/tesseract-ocr, SHA-256 verified). Both only run when the user runs the model download command or enables download. No telemetry, no document upload found. The app does not send user data; the statement should say so. |
| 11 | System config changes need warnings | Partly | The installer adds to the user PATH only via an opt-in task (`/TASKS=addtopath`). Confirm the task is unchecked or clearly labelled by default in evrakci.iss. |
| 12 | Installer has uninstall instructions or facilities | Met | evrakci.iss has an uninstall entry (`unins000.exe`, "Evrakçı'yı kaldır"); windows-installer.yml tests install, upgrade and uninstall. |
| 13 | MFA for all team members on SignPath and the source repo | Missing (owner only) | Cannot be seen from the repo. The owner must enable it on GitHub and SignPath. |
| 14 | Roles: Authors, Reviewers, Approvers; non-committer changes reviewed; each signing request approved by a trusted team member | **Missing** | No roles page. CONTRIBUTING.md has no review rules. The CLA assistant workflow exists (cla.yml) but no branch protection or approver is documented. |
| 15 | A "Code signing policy" published on the home and download pages, listing roles and privacy info | **Missing** | No website, no GitHub Pages (`has_pages` false, homepage empty), no README section. |
| 16 | Must accept SignPath constraints; assist with investigations | Owner decision | Nothing to build. |
| 17 | Ask upstream libraries to get their own signatures | Owner decision | Note in the policy page. |

Typical items from the task brief, not found in the pages I opened (unverified):

| Item | Status | Evidence |
|---|---|---|
| Public repository | Met | github.com/ZackHaronOriginal/Evrakci is public. |
| Project website | Missing | None exists. |
| CI that SignPath supports, artifacts uploaded from CI | Partly | windows-installer.yml builds on windows-latest and uploads `Evrakci-Kurulum` with actions/upload-artifact (the SignPath action needs this artifact id). No signing step yet. |
| Sign only tagged releases | Partly | The workflow triggers on `tags: v*` and checks tag equals `__version__`, but it also runs on main, `claude/**` and PRs. The signing step must be limited to `refs/tags/v*`. |
| SignPath GitHub Action and app integration | Missing | No SignPath step. Workflow permissions are `contents: read` only. |

## Blocking issue to decide first

The licensing plan (commercial licences through the CLA, closed Pro modules) conflicts with requirements 2 and 3 as written on signpath.org/terms. The owner must either drop commercial dual-licensing and the closed Pro modules for this project (and edit CLA.md, CONTRIBUTING.md, docs/licensing.md, README licence section), or give up the SignPath free plan. This is a business decision, not something to patch quietly. SignPath may answer questions about edge cases; ask on the apply form.

## What to create (smallest compliant artifacts)

1. **Project website**: a `docs/` site on GitHub Pages (Settings, Pages, source "main /docs"; or a `gh-pages` branch). Note docs/ already holds internal markdown, so use `docs/index.md` plus a `_config.yml`, or a separate `site/` folder with Pages from a workflow. Minimum pages:
   - Home: what Evrakçı does, link to downloads, and a "Code signing policy" link.
   - Download page: link to the latest GitHub release installer plus SHA-256, and the line "Free Windows code signing provided by SignPath.io, certificate by SignPath Foundation".
   - Code signing policy page (text below).
   - Privacy statement page (text below).
2. **"Code signing policy" section** in README.md (and README.tr.md) and on the website home and download pages, using that exact term. Content:
   - Free code signing provided by SignPath.io, certificate by SignPath Foundation.
   - Roles: Authors = committers listed in the repo; Reviewers = (owner to name); Approvers = (owner to name). Non-committer pull requests are reviewed before merge.
   - Signed only: the Windows installer built by GitHub Actions from a `v*` tag on main.
   - Link to the privacy statement.
3. **Privacy statement** (README section and site page): "Evrakçı does not send your documents or any personal data anywhere. It makes network requests only when you run the OCR model download (`evrakci ocr-modelleri-indir` / the download action), to fetch OCR model files from the official rapidocr and Tesseract (raw.githubusercontent.com/tesseract-ocr) locations, each verified by SHA-256. There is no telemetry or update check." Confirm the sentence about the UI download action by grepping the GUI before publishing. If the GUI can start a download automatically, add an off switch or say it is user-triggered.
4. **Licensing text changes** (owner decision above): remove commercial relicensing and closed-module wording from CLA.md section 2, CONTRIBUTING.md and docs/licensing.md, or keep the plan and skip SignPath.
5. **Contributor and review rules** in CONTRIBUTING.md: every non-committer change reviewed by a team member; MFA required for team members; branch protection on main (require PR review).
6. **Release**: push a `v<version>` tag matching `evrakci.__version__` and publish a GitHub release so the signed form "is already released". Confirm exe version metadata (product name, version, company).
7. **Workflow change** in .github/workflows/windows-installer.yml, after the "Build installer" step and the upload-artifact step (give the upload step an `id`):
   - Add `id-token: write`? Not verified. Follow the SignPath docs for the exact permissions and action inputs (expected: `signpath/github-action-submit-signing-request`, inputs `api-token`, `organization-id`, `project-slug`, `signing-policy-slug`, `github-artifact-id`, `wait-for-completion`, `output-artifact-directory`). Unverified from an opened page.
   - Guard it: `if: startsWith(github.ref, 'refs/tags/v')`.
   - Use secrets only: `${{ secrets.SIGNPATH_API_TOKEN }}` and repo variables for the organization id and slugs. Never commit tokens.
   - Install the SignPath GitHub App (trusted build system) on the repo; the owner configures it in SignPath.
   - Upload the signed installer as the release asset.
   - Keep PR and branch builds unsigned.

## Owner-only steps

- Decide the licence question (item above).
- Apply on SignPath's form (https://signpath.org/apply) after the website, policy page, privacy statement and a tagged release exist.
- Enable MFA on the GitHub account, and on SignPath when the account is created. Require it for any other team member.
- Choose who the Reviewers and Approvers are (the approver must be trusted by the whole team; as a solo maintainer, say so on the policy page and ask SignPath whether that is acceptable).
- Add the SignPath secrets (`SIGNPATH_API_TOKEN`) and variables in GitHub, install the SignPath GitHub App, and turn on GitHub Pages.
- Turn on branch protection for main.
