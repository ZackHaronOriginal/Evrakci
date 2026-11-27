# 05 — Sharing work over a local network: options, failures, and a path for Evrakçı

Scope: how small-office desktop apps let several Windows PCs share work without the cloud, what has gone wrong for others, and what Evrakçı's job format must look like now so that sharing later does not force a rewrite. Every claim has a source next to it. Where I could not find a primary source, the claim is marked **(unverified)**.

## 1. The core fact: a file share is not a database

Every vendor that has had to deal with this says the same thing. Software that writes in place to shared state (a database file, a catalog, an index) breaks in ways that are rare, hard to reproduce, and expensive when they happen.

- **SQLite's own docs** say a database on a network filesystem "often leads to various kinds of trouble and grief". The failures are "not frequent or repeatable", so early testing looks fine. Network filesystems can store writes "out of time order", and their sync and locking behaviour "vary among implementations and installations". The docs advise a client/server database, or a proxy process running on the machine that holds the file. https://www.sqlite.org/useovernet.html
- **WAL mode cannot work on a share at all.** WAL needs shared memory, and "processes on separate host machines obviously cannot share memory". https://www.sqlite.org/wal.html
- **Buggy locks lead to corruption.** "Some filesystems contain bugs in their locking logic … This is especially true of network filesystems". A background backup that copies a database in the middle of a transaction can also produce a corrupt copy. https://www.sqlite.org/howtocorrupt.html

The same pattern shows up in commercial products:

- **Lightroom Classic** will not open a catalog (a SQLite file) on a network volume. Adobe's catalog FAQ, as quoted on the Adobe forums: "you can't store catalogs on a network, but you can store or share your photos on a network". The common workaround is to copy the catalog to a local disk, work on it, and copy it back. https://community.adobe.com/t5/lightroom-classic-discussions/lightroom-cannot-launch-with-this-catalog-it-is-either-on-a-network-volume-or-on-a-volume-on-which/m-p/15170097 (I could not fetch the helpx FAQ directly, HTTP 403, so the exact Adobe wording comes second-hand: **unverified at primary source**.)
- **Microsoft Access** on a share runs into SMB2 leasing. Microsoft's "inconsistent state" article gives the workaround of disabling leasing on the machine that hosts the back-end file. https://support.microsoft.com/en-us/access/access-reports-that-databases-are-in-an-inconsistent-state . The `DisableLeasing` registry value is documented in KB 2957623. https://support.microsoft.com/kb/2957623
- **Opportunistic locks (oplocks)**, which let a client cache data from the server, have caused corruption for shared database files for decades. Samba's documentation names database software as the main case and suggests turning oplocks off for those shares. https://web.mit.edu/samba/swat/help/Samba3-HOWTO/locking.html . Red Hat lists "a database application whose vendor recommends it" as a reason to disable them. https://access.redhat.com/solutions/3199302 . On a small NAS that nobody administers, staff cannot be expected to change these settings.
- **Obsidian** staff say vaults on network drives are not supported. Network mounts "lack some FS feature", mainly change notification. Users report missed changes in SMB subfolders and crashes on vaults at a share's root. https://forum.obsidian.md/t/obsidian-crashes-when-vault-is-located-on-network-drive/30700 , https://forum.obsidian.md/t/subfolder-file-changes-not-detected-in-smb-share-vaults/59326 , https://forum.obsidian.md/t/opening-vault-from-nas-stopped-working-with-1-13-4-network-drive/116739

**Lesson for Evrakçı:** never keep a live SQLite file, or any file rewritten in place, inside a job folder that will sit on a share. JSON manifests plus page and image files are the right starting point. They are only safe if the write pattern is safe (section 4).

## 2. Option A: jobs on a shared SMB folder or NAS, opened directly

### How others make it work

**Lock files next to the document.** This is the most common pattern for small offices.
- Microsoft Office creates a hidden owner file `~$name` in the same folder. That file produces the message "locked for editing by <user>". If Office crashes, the file stays behind, and Microsoft's fix is to check that nobody has the document open and then delete the owner file. https://support.microsoft.com/en-us/kb/313472 , https://learn.microsoft.com/en-us/archive/blogs/the_microsoft_excel_support_team_blog/the-definitive-locked-file-post-updated-772014
- LibreOffice writes `.~lock.<file>#` (on Windows, without the leading dot). Over SMB it often reports "locked by Unknown User", and locks survive crashes. https://ask.libreoffice.org/t/files-on-remote-shares-are-always-read-only/76565 , https://www.linuxquestions.org/questions/linux-software-2/libreoffice-document-is-locked-for-editing-by-unknown-user-4175699967/
- AutoCAD writes `.dwl`/`.dwl2` files that record who has a drawing open (used by WHOHAS). Forum threads are full of stale locks after crashes and of sync tools that ignore them. https://forums.autodesk.com/t5/autocad-forum/autocad-2018-freezes-creates-dwl-dwl2-files-and-locks-files/m-p/8021804 , https://forums.autodesk.com/t5/autocad-forum/autocad-and-google-file-stream-file-locking-dwl-and-dwl2/m-p/8514748

**Merge on save instead of locking.** KeePass 2.x checks at save time whether the file on disk changed since it was loaded. If it did, KeePass offers to synchronize (merge, newest entry wins) or overwrite. The docs say plainly that without care "users need to be careful to not overwrite each others changes". https://keepass.info/help/base/multiuser.html

### What goes wrong
- **Stale locks.** Crashes, sleep and pulled cables leave lock files behind, as every product above shows. Users then need a safe way to take a lock over.
- **"Unknown user" locks.** Lock owners come out wrong or blank when the lock file is created under one account and read under another, or when the server does not pass the name through (LibreOffice and Office threads above).
- **Antivirus.** On-access scanners open newly written temp files. The rename that follows then fails with a sharing violation and succeeds on retry. https://support.microfocus.com/kb/doc.php?id=7004693 . NetApp documents rename failures and timeouts on large files when share scanning is on. https://kb.netapp.com/on-prem/ontap/da/NAS/NAS-KBs/SMB_Rename_of_large_zip_files_may_fail_with_internal_error_due_to_VSCAN_timeout . Syncthing users hit the same failure on Windows shares. https://forum.syncthing.net/t/not-renaming-tmp-files-in-win10/17863
- **Renames are not reliably atomic over SMB.** A Samba bug reports a race in MoveFile/MoveFileEx against Samba shares. https://bugzilla.samba.org/show_bug.cgi?id=13648 . Python's tracker and the Go issue tracker disagree about how atomic replace-rename is on Windows. https://bugs.python.org/issue8828 , https://github.com/golang/go/issues/8914 . Design rule: write to a temp file, flush, rename, read back to verify, and retry on failure.
- **Offline Files / Sync Center.** These can give a user a cached copy that conflicts with the server copy later. I found no Microsoft deprecation notice. Microsoft describes its successor, Work Folders, as user-data only, "does not support team shares or collaboration". https://techcommunity.microsoft.com/t5/Storage-at-Microsoft/Comparing-Work-Folders-and-Offline-Files/ba-p/425582 . The claim that Offline Files corrupts multi-file job folders is my inference **(unverified)**. The safe default is to tell offices to exclude the Evrakçı share from Offline Files.
- **No change notification.** Watching for changes on a share is unreliable (Obsidian, above), so an app must rescan or poll rather than trust file-watch events.

### Verdict on A
Option A suits *storage and handoff*: large immutable files plus small manifests that are written whole, once. It does not suit *live concurrent editing*. It needs no extra software, and the office already has the share and its backups.

## 3. Option B: one PC or the NAS runs a server

### Examples
- **QuickBooks Desktop** is the closest analogue: a desktop app that started on a file share and moved to a server. The "Database Server Manager" must run on the computer that stores the company file. Hosting mode is set per computer and per QuickBooks version, and each version has its own database service (e.g. QuickBooksDB34 for 2024). Clients find the server through a small `.nd` file next to the data file. A whole family of support errors (H101/H202/H303/H505) covers clients that cannot reach the host. https://quickbooks.intuit.com/learn-support/en-us/help-article/multi-user-mode/hosting-company-data-multi-user-mode-quickbooks/L6vU3qBNE_US_en_US , https://quickbooks.intuit.com/learn-support/en-us/help-article/install-products/use-quickbooks-database-server-manager/L1oLSsAZ1_US_en_US . The `.nd` file is worth copying: the share holds a small pointer that tells clients which host to talk to.
- **Turkish accounting software.** Logo products run on Microsoft SQL Server, which must be installed in mixed authentication mode with an `sa` password. https://docs.logo.com.tr/download/attachments/66244203/SQL%20Kurulum%20ve%20Veritaban%C4%B1%20Ba%C4%9Flant%C4%B1%20%C4%B0%C5%9Flemleri.pdf?api=v2 . Logo's requirements note that SQL Server Express is capped at 10 GB in total and say Logo does not recommend Express for production. https://docs.logo.com.tr/download/attachments/50679743/wings_sistem_ihtiyac.pdf?api=v2 . A Netsis forum thread shows the usual support work: clients cannot reach the SQL server until a firewall rule is added. https://forum.netgate.com/topic/40243/netsis-cl%C4%B1ent-kurulum-hatasi . In Turkey this setup work is normally done by the vendor's authorised dealer (bayi) **(unverified, industry knowledge)**. Mikro and Luca: no primary sources found on their network architecture **(unverified)**.
- **Paperless-ngx**, the open-source document archive, is Linux-only: "Windows is not and will never be supported". It is installed through Docker Compose. https://github.com/paperless-ngx/paperless-ngx/blob/d8858ce5c6a8c927cd73ee80e1d610da24aba39f/docs/setup.md (an older doc snapshot).
- **Nextcloud Server** "does not support Microsoft Windows" and recommends a VM or Docker. https://nextcloud.com/install/ , https://docs.nextcloud.com/server/stable/admin_manual/installation/system_requirements.html
- **Syncthing-style peer sync** avoids a server, but concurrent edits become `.sync-conflict-<date>-<time>-<device>` copies, and the copy with the older modification time loses. https://docs.syncthing.net/users/syncing.html . That works for single files. For a job that spans many related files it is dangerous: page cuts from one PC can end up mixed with review state from another.

### Costs for an office with no IT staff
- **Firewall.** Windows blocks unsolicited inbound traffic by default, and an app needs an inbound rule, usually added by its installer. Allowing it on the Private profile is the narrow choice. https://learn.microsoft.com/windows/security/operating-system-security/network-security/windows-firewall/rules , https://support.microsoft.com/en-gb/help/4525108/security-risks-of-allowing-apps-through-windows-defender-firewall . If Windows marks the office network as Public, the server cannot be reached until someone changes it.
- **Discovery.** Windows has had native mDNS since 10 1703, but the desktop API surface and its quirks are uneven. https://techcommunity.microsoft.com/blog/networkingblog/mdns-in-the-enterprise/3275777 . A pointer file on the share, QuickBooks `.nd` style, is simpler and more reliable.
- **The host PC must stay on.** If the "server" is a staff PC, sleep, reboots and Windows Update take everyone offline. This is the root cause behind QuickBooks' H-series errors (above).
- **Version skew.** QuickBooks ties hosting to a specific version per machine (above), and Logo-style SQL schemas are upgraded centrally. A client/server Evrakçı would need a protocol version check and a clear "please update" message.
- **Backups.** A database server needs dump-based backups. A plain file copy of a live database is unsafe (SQLite howtocorrupt above, and the same holds for PostgreSQL in general **(unverified for PG specifically here)**). Files on a share, by contrast, are covered by whatever backup the office already runs.

### Verdict on B
B is the right *eventual* answer only if Evrakçı needs real-time multi-user editing of one job, or search across tens of thousands of jobs. For a handful to a few dozen staff, the install, firewall, always-on host and backup work are exactly what an office without IT handles worst.

## 4. Option C: local work plus publish/check-in to a shared place

This is lock-modify-unlock, the model Subversion uses for files that cannot be merged. A lock exists "to minimize wasted time and effort". Anyone can *break* a lock, and *stealing* it ("breaking and relocking … in one atomic step") is an ordinary operation. The previous holder sees their lock marked broken or stolen. Locks are described as "a communication tool". https://svnbook.red-bean.com/en/1.7/svn.advanced.locking.html . The Lightroom copy-local, copy-back workaround (above) is the informal version of the same idea.

How it would work in Evrakçı:
1. **Check out (Üzerime al).** Write a lock record into the shared job folder: user, PC name, time, app version. Copy the job, or only its mutable parts, to a local working folder. Large immutable scans can stay on the share and be read from there.
2. **Work locally** at full speed. SQLite or anything else is fine locally.
3. **Check in (Gönder/Teslim et).** Write the new manifest files to temp names on the share, flush, rename, verify, then release the lock. Bump a `revision` counter.
4. **Conflict rule.** On check-in, if the share's `revision` is not the one checked out (someone took the job over), never overwrite. Save the work as a sibling copy or new revision and show both, as KeePass does with its synchronize-or-overwrite prompt and Syncthing with conflict copies (above).
5. **Take over (Devral).** When a lock is older than N minutes, or its heartbeat has stopped, the UI shows "Ayşe has had this job open since 10:42 on PC-3, take it over?". Taking over steals the lock, SVN-style, and the original holder is told on their next save. This is the safe version of Microsoft's "delete the owner file" advice (above).

Option C keeps every write on the share small, whole-file and rare, which avoids the oplock, partial-write and antivirus failures described above. It needs no server.

## 5. State, tags, ownership: keep the model small

Each job manifest carries:
- `state`: a short fixed list. Example: `taslak` (draft) → `devam` (in progress) → `kontrol` (in review) → `bitti` (finished) → `gönderildi` (sent, set by hand). Each change is logged with who and when.
- `owner` (responsible person), separate from `lock` (who has it open now). Office's "locked for editing by" message works because it answers one question, so the UI should keep "who is responsible" and "who has it open" as two separate, visible facts.
- `tags`: free text, used sparingly.
- An append-only `history` of check-ins, state changes and takeovers.
- `outputs/`: final exports. "Find finished files to send" becomes a filter on `state = bitti` that opens `outputs/` in Explorer.

Staff never need to learn the word "lock". Two buttons are enough: "open for editing" and "take over".

## 6. Recommendation for Evrakçı: a staged path

**Stage 0 (now, single PC).** Keep folders plus JSON, but adopt the format below from day one. Point the job root at a configurable path, defaulting to local. A local SQLite index is fine as long as it is a *cache* that can always be rebuilt by scanning manifests, never the source of truth.

**Stage 1 (sharing, no server).** Let the office set the job root to a share (`\\NAS\Evrakci\İşler`). Add check-out/check-in, lock records with heartbeat, takeover, and a list view that rescans manifests on a timer, because file watching cannot be trusted on SMB (section 2). Document three office settings: exclude the share from Offline Files, add an antivirus exception for the Evrakçı temp-file pattern if renames fail, and back up the share. This covers the owner's whole wish list (share, view others' work, take over, state tags, find finished outputs) without a server.

**Stage 2 (only if needed).** If the office grows, or wants real-time co-editing or fast search across years of jobs, add an optional "Evrakçı host" mode on one always-on PC or the NAS. Announce it with a pointer file on the share (QuickBooks `.nd` style), check protocol versions, and keep the *same* job folders as storage. The host then only coordinates locks and indexing. Do not start here.

### Job storage format: must-haves from day one
1. **A job ID that never changes** (UUID) in `job.json`, separate from the folder name, so renames and moves do not break references.
2. **`schema_version`** in every JSON file, plus a reader that refuses newer versions it does not understand. This is protection against version skew between PCs.
3. **A strict split between immutable and mutable data.** Scanned PDFs and page images are written once and never rewritten. Their names are content-addressed or never reused, so two PCs can never both write the same file. Mutable state (cuts, template values, review, state, tags) lives in a few small JSON files.
4. **Only whole-file, atomic-style writes:** write to temp, flush, rename, verify, retry on sharing violation. Never append to or patch a file in place on the share.
5. **A `revision` counter and `updated_by`/`updated_at`** in the manifest, so check-in can detect conflicts.
6. **The lock as its own small file** (`lock.json`: user, machine, started, heartbeat, app version), never a field inside the manifest. Locks are created, refreshed and deleted far more often than the manifest changes.
7. **Relative paths only** inside the job. No `C:\Users\...` paths, so the folder can move between a PC and a share.
8. **No SQLite or other binary database inside job folders.** Any index lives per PC and can be rebuilt (sections 1 and 6).
9. **`outputs/`** as a known subfolder, and **`history.jsonl`** as an append-only log. Each history line is written by the lock holder only, or each check-in writes its own file, to avoid concurrent appends.
10. **The user's identity** (display name plus Windows username plus machine name) recorded on every change. That makes "who has this open" and "who finished it" answerable without a login server.

With these rules, moving from Stage 0 to Stage 1 means changing where the job root points and adding the lock and check-in UI. The data model does not have to change.
