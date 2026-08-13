---
name: clinical-change-control
description: >-
  The non-negotiable hard gates of a clinical EHR-automation workflow, each paired with
  the real incident that created it. LOAD THIS FIRST — before running or modifying any
  of the clinic pipeline commands; before any scribe-session capture, archive, or
  cleanup; before any chart-file merge; before trusting any capture/OCR "PASS"; before
  proposing a new capture path or browser surface; and any time you are tempted to skip,
  weaken, or "temporarily" bypass a gate. If a gate blocks you, this skill tells you why
  stopping is the correct output.
---

# clinical-change-control — the hard gates and why they exist

You are about to touch a workflow that moves real patient data (PHI) between a
cloud-based EHR, a BAA-covered LLM scribe surface, and an encrypted local disk (the
Patient Drive). Every gate below was paid for with a real incident or a red-team
finding. **None of them are style preferences. If a gate is inconvenient, the gate is
working.**

The single most important fact to internalize before anything else:

> A capture pipeline once reported `status: PASS` on two independent runs while having
> captured **14 byte-identical copies of the EHR vendor's marketing/pricing page**
> instead of the patient's documents. The manifest checks passed. An adversarial
> red-team review passed. A frontier-model review passed. The error was caught only when
> a human opened one of the PDFs. — *"Precision good, accuracy bad — did you actually
> read it?"*

Careful reasoning about status fields did not catch that. Opening the payload did. That
asymmetry is why these gates exist and why you must not reason your way around them.

---

## Vocabulary — defined once

| Term | Meaning |
|---|---|
| **The EHR** | The cloud-based electronic health record where real charts live. |
| **Patient Drive** | The encrypted disk-image volume. The ONLY place PHI may be written outside the EHR and the scribe session. |
| **PHI** | Protected Health Information — names, DOBs, chart contents, source chats, schedule rows. |
| **The no-PHI rule** | The standing hard rule: no PHI in the (cloud-synced, unencrypted) knowledge base, ever. PHI lives only on the Drive / in the EHR / in the BAA-covered scribe session. |
| **The Scribe** | The BAA-covered LLM product, signed into the clinician's covered account. The consumer version of the same product is NOT covered. |
| **BAA** | Business Associate Agreement — the legal cover that makes the scribe usable for PHI. It rides the **account login**, not the browser profile. |
| **slug** | A patient's folder name under `<Drive>/patients/<slug>/`. |
| **chart.json** | The structured per-patient chart file — source of truth for kickoff prompts. Its merge history is **append-only**. |
| **source-chat** | The saved raw text of a scribe conversation, under `patients/<slug>/source-chats/`. |
| **app-shell** | The EHR's generic application/marketing page that a broken fetch silently returns instead of a real document. |
| **Status buckets** | `UNMAPPED` (identity not proven — don't touch), `BLOCKED_BROKEN_SOURCE` (capture invalid — leave session open, surface immediately), `NEEDS_BACKFILL` (source saved but no chart.json), `NEW_OR_UNRESOLVED` (no patient folder — don't invent one), terminal **lost-source** (source unrecoverable). |

---

## Before you run anything — preflight checklist

Run at the top of EVERY session that touches the pipeline. Do not start with any box
unchecked.

- [ ] **1. Read the command file you are about to execute in full, including its STATUS banner.** A broken sub-path gets a banner in the live command file; banners outrank memory.
- [ ] **2. Verify a genuine Patient Drive mount** — run the mount-sentinel command (Gate 2) and require `MOUNT_OK`. A directory existing at the mount point proves nothing. A volume that is still mounted after its backing-store file has been unlinked also proves nothing.
- [ ] **3. Confirm an attested isolated browser surface** — a dedicated browser instance with its own profile, attested by inspecting the OS process/socket. Never the clinician's daily browser. Cannot attest → STOP (Gate 3).
- [ ] **4. Confirm the destination is the BAA-covered scribe account** — not the consumer product, not another account. Unclear = stop and stage files on the Drive for manual paste (Gate 4).
- [ ] **5. If running kickoff:** run the synthetic smoke test first (a test patient through the prompt builder). If it fails, stop; do not build real prompts on a broken pipeline.
- [ ] **6. Know your escalation posture:** on ANY gate failure or ambiguity, **stop and report** — which step, which surface was active, exact error, whether anything was written to the Drive. Never improvise an alternate path. **Stopping is a successful outcome; a workaround is not.**
- [ ] **7. PHI containment set:** commit that patient names, schedule rows, chart JSON, source chats, and prompt content will appear ONLY in files on the Drive — never in the knowledge base, scratch files, stdout, or your chat replies. Final reports carry **counts, status buckets, and the output folder path only** (Gate 1).
- [ ] **8. Report filenames carry a date + session/agent stamp** (e.g. `census-<date>-<session>-report.md`), never a bare canonical name. Two agents once silently clobbered the same canonical report filename in the same week the shared task register saw a live concurrent-writer race. Concurrent sessions are the norm — stamp every report so a collision is impossible, and treat any unstamped report you find as possibly-clobbered.

---

## The gate table

| # | Gate | Rule | Incident behind it | Failure if skipped |
|---|---|---|---|---|
| 1 | **PHI containment** | PHI exists only in the EHR, the scribe session, and the Drive. Never the knowledge base, scratch, stdout, or chat replies. Reports = counts + buckets + folder path only. | Standing hard rule; the in-repo test scaffold's patient-capable folders were deliberately evacuated from the synced knowledge base for exactly this reason. | PHI lands in a synced, unencrypted, multi-agent-readable location — an unrecallable disclosure. |
| 2 | **Mount sentinel before every write batch** | Before EVERY batch of writes: confirm the volume is mounted, the backing-store file still exists at its exact path, the disk-image tool reports that same path, and a byte-read of the sentinel is not all-NUL. `MOUNT_FAILED` → STOP, no writes. Dir-exists is NOT a mount check — **and a mounted volume is not one either.** | Red-team finding, then an upgrade: if the disk image unmounts mid-run (sleep/disconnect), the mountpoint can persist as an ordinary directory on the boot volume. Later, the old `mount \| grep` + `test -f` one-liner returned `MOUNT_OK` for four hours after the disk-image file had been unlinked from its path — the volume stayed mounted and reads returned sparse zeros. | Writes land as **unencrypted PHI on the boot disk** while every path string still "works" — or land in a volume whose backing store is gone, reading back as zeros. |
| 3 | **Attested isolated surface — never the daily browser** | All EHR/scribe browser work runs on an attested isolated surface: a dedicated browser **process** with its own user-data-dir, attested via the OS (process command line / socket ownership) — never the clinician's daily browser. Cannot attest → STOP; anything from an unattested surface **does not count**. | Automation driving the daily browser caused screen-blink/focus-steal/mid-keystroke edits during a live patient visit. It **recurred** when an agent's global config default silently preferred the daily-browser backend at a branch point — an agent-side routing bug, structurally impossible in a transport that dials one dedicated port and has no branch. | The clinician's live browser is hijacked mid-visit; captures come from an unverified surface; the run's outputs are untrusted. |
| 4 | **BAA surface verification — by evidence probe, never by memory** | Verify the session is the covered scribe product in the covered account, and verify it with a **read-only probe that takes seconds** and must positively identify the covered workspace. A probe returning a consumer plan or a null workspace is a STOP. Never offer the operator a "confirm it from memory" option — that is a bypass wearing the costume of a question. Consumer product / other account / unclear → stop; leave ready-to-paste files on the Drive and report the folder path. | BAA rides the account login, not the browser profile — so "it's in a browser we control" proves nothing about coverage. In the originating setup the dedicated, socket-attested profile — a clean Gate 3 PASS — was found signed into a personal, non-BAA account with no covered workspace on the login at all, and that session had offered a memory-based clearance option before any probe ran. | PHI is pasted into a non-BAA surface — same category of harm as Gate 1. **A Gate 3 PASS is not evidence for Gate 4:** an isolated, attested, dedicated surface can be signed into entirely the wrong account. |
| 5 | **Wrong-chart guard (before capture)** | Before capturing, confirm the chart open in the browser is the intended patient — verify name + DOB. Mismatch → abort. The capture harness has NO identity check of its own. | Nothing in the capture mechanics knows *whose* chart is open. | Patient B's documents land in Patient A's folder — cross-contamination no downstream count or checksum will ever flag. |
| 6 | **Payload-reality Gate 0** | After ANY capture and before trusting ANY green status: **open ≥1 captured document and confirm it is real clinical content** — not app-shell, marketing, pricing, or error chrome. `status: PASS` is necessary, never sufficient. | The headline incident: manifest PASSED 14 byte-identical app-shell/pricing pages on two independent runs; magic-byte + text-extraction checks passed; manifest review, red-team, and frontier-model review all missed it; a human opening one PDF caught it. | An entire category of source data is **silently omitted while the pipeline reports PASS** — invisible until it matters clinically. |
| 7 | **Content-valid save + same-day capture** | A saved source must be the actual **message thread** — ≥1 clinician turn AND ≥1 assistant turn of patient-specific content. Sidebar/chat-list/UI captures, home/redirect pages, and empty files FAIL. "File exists" ≠ "source saved." Capture and validate **same-day**; never rely on re-opening a saved URL later. Invalid capture → `BLOCKED_BROKEN_SOURCE`, leave the live session OPEN (it is the only remaining copy), surface **immediately with the still-open URL** — not in the final report. | A remediation sweep found 18 blocked patients whose "saved" files were almost all sidebar/UI captures; on re-export, **17 of 18 saved scribe URLs redirected to the home screen with no thread.** Best explanation: the platform ages conversations out (operationally adopted, not formally proven). | The active list gets cleaned up against worthless backups; the platform ages the real source out; the clinical record of the visit is gone. |
| 8 | **Identity quote (before archive or chart update)** | Archiving or a chart update requires a **specific quoted line from the thread** (name / DOB / explicit patient reference) tying the thread to the slug. Weaker basis → `UNMAPPED`; do not archive, do not merge. | Red-team finding: the content-valid check (Gate 7) validates thread *shape*, not *whose* thread it is — a perfectly valid thread filed under the wrong slug passes content + placement checks. | A real visit is written into the **wrong patient's** append-only chart and drives that patient's future summaries. |
| 9 | **OCR spot-check** | After OCR, read the OCR text of **≥2 scanned PDFs against the source images**. `ocrReviewCount: 0` means nothing tripped an auto-flag heuristic — NOT that the OCR is correct. | A confidently-wrong OCR (transposed dose, flipped date) produces clean-looking text with no error signal anywhere. | A wrong dose or date enters the chart silently and reads as fact forever after. |
| 10 | **Delta review before merge — narrative fields carry the weight** | The model-generated chart-update JSON is reviewed BEFORE the merge script runs: show the clinician the delta, with review weight on the **narrative continuity fields** (interval history, visit note, titration summary) — those are what the clinician reads, and the one thing the EHR's live medication administration record (MAR) can't cross-check. Medication fields merge as *advisory continuity, not the prescribing source* — the authoritative multi-provider MAR is reconciled live at read-time, so a med-field error is caught there; med removals/decreases surface as non-blocking diff flags. Never re-merge a session already marked merged (append-only — double-posting is permanent). | Red-team finding: the merge is append-only — a merged change is permanent chart history propagating into every future summary. The tiering decision (narrative = blocking review, meds = advisory flag) came from analyzing which errors the live MAR would and wouldn't catch. | A wrong **narrative** ("what was done last time") misleads the next visit's orientation — and nothing downstream ever cross-checks it. |
| 11 | **Human sign gate** | Captured bundles, OCR output, and scribe-session output are **drafts**. Nothing reaches the clinical chart without the clinician's review and sign-off. The pipeline never autonomously charts. | The design premise of the whole workflow: a workflow with a human sign gate, not an autonomous agent. | The system becomes an unsupervised prescriber's assistant writing to legal medical records. |
| 12 | **Archive-only — NEVER hard-delete** | Cleanup of scribe sessions is archive/hide only. Hard delete is the ONE irreversible action in the workflow and is out of scope for any agent acting on its own judgment. (One narrow, six-condition staged-purge exception exists for pre-staged quarantine folders — staged-first with a manifest, eligible content only, double-keyed same-session approval naming the exact path, read-back with one final yes, sentinel before + verify after, manifest preserved to a deletion-record first.) Archive only after full per-session proof (Gates 7 + 8, chart status, longitudinal rebuild) AND an explicit yes to an archive question asked *after* verification. `UNMAPPED` / `BLOCKED_BROKEN_SOURCE` / ambiguous sessions stay OPEN. | Designed specifically so the workflow is safe on a low-reasoning background model. Combined with Gate 7's source-decay finding, a wrong delete = permanent loss. | The only copy of a clinical source is destroyed by an agent that misjudged a verification — unrecoverable by construction. |
| 13 | **Empty-payload block — mechanical, BEFORE the delta review is generated** | A merge payload whose visit note asserts the *absence* of content is not an approvable delta — it is a refusal, and refusals never merge. Test **positively**, not with a phrase blacklist: a note may merge only if it contains ≥1 clinical token grounded in the chart — a medication name drawn from that patient's own med list, a numeric dose, a monitoring value, or a dated follow-up interval. Zero grounded tokens → `BLOCK_EMPTY_PAYLOAD`; do not surface it for approval at all. Refusal has exactly ONE legal home in the schema: a top-level `error` field. A refusal appearing anywhere else — especially inside the visit note — is a **schema violation**, not a content judgment call. | A six-session merge batch merged five updates; **four had written refusal boilerplate into the visit history as the clinical note** ("Post-visit clinical details were not provided…"). The one session that *was* caught had emitted `{error: …}` — caught precisely because the schema gave its refusal a legal home. The delta review ran, the clinician was told which delta was substantial, and approved anyway — **the failure survived human review, which is why this gate must be mechanical and must run upstream of the review doc.** Root cause is a category error: the payload-reality gate asks "is this content *real*?" (catching fabrication) and has no concept of "is there content *at all*?" A refusal is honest and empty — the mirror-image failure — so every check built to catch dishonesty passes it. | Refusal text becomes permanent chart history in an append-only record, then propagates into the rebuilt longitudinal summary — the artifact actually read at the next visit — where it reads as a documented finding of "nothing happened" rather than as a pipeline failure. |
| 14 | **Date coherence — and corrections must be applied RECURSIVELY** | Every date anywhere in a merge payload — including inside nested narrative objects — must be **≤ the encounter date**. A future-dated field relative to its own visit is a block, not a flag. When a date is corrected during review, apply the correction to **every occurrence in the payload**, not only the top-level visit date; re-scan the whole payload after any correction. | In the same batch, **four of five model-emitted visit dates were wrong or blank.** The review doc corrected them — but only at the top level. The same wrong date survived one level down and merged: a last-medication-change date two days *after* its own visit, in the one chart of the batch carrying real clinical content. Four obviously-empty notes are self-evidently non-clinical and easy to spot; **a plausible wrong date on true content is the one that survives review.** The generalizable defect is not about dates: *a correction applied at the top level and not recursively is a defect pattern, not a one-off.* | The next visit is oriented by a false medication-change date — a prescribing-relevant error that, unlike a bad med *value*, the live MAR does **not** cross-check (Gate 10's tiering assumes the MAR catches med errors; it does not catch a wrong date on a real change). |
| 14b | **Array item shapes — block, never coerce** | Every schema array must carry the right ITEM TYPE. Diagnoses, medications, visits, and interim events are arrays of **objects**; open items, risk flags, monitoring-due entries, and manual corrections are arrays of **strings**. A shape-wrong payload is **blocked, never coerced** — it is a defect of the source reply, the same class as a refusal in the visit note, so regenerate the reply. Hand-editing a payload to pass a screen stays forbidden. Coercion is legitimate in exactly one place: pre-existing on-disk degradation, where there is no author to send it back to. Run the check in the pre-merge screen, upstream of Gates 13 and 14. | A chart-update payload emitted diagnoses as bare strings. It cleared Gates 13 and 14 and the identity gate, merged into append-only history, and the longitudinal renderer then crashed dereferencing a string as an object. The repair was a disclosed direct chart edit. Nothing upstream could have caught it: the JSON-schema library was not installed on that host, and the dependency-free fallback validator item-shape-checked one array out of eight. Third occurrence of the same defect family. | A schema violation reaches append-only chart history and takes out the renderer that produces the artifact actually read at the next visit — and the repair itself becomes an ungated hand edit. |

---

## The pre-merge payload screen (Gates 13, 14, 14b)

These run **before** the delta-review doc is generated, not as extra items in it. A payload that fails either one never reaches the approval queue — the whole point is that the incident batch *did* reach it and was approved.

Order of operations for any merge batch:

1. **Screen every payload mechanically** — item shapes (Gate 14b) first, then the grounded-token test (Gate 13) and date coherence (Gate 14). Shape runs first because a shape-wrong payload can't be meaningfully screened for content.
2. **Bucket the failures, don't fix them:** `BLOCK_SHAPE_INVALID`, `BLOCK_EMPTY_PAYLOAD` or `BLOCK_DATE_INCOHERENT`. A blocked payload means *the session had nothing to say* or *the model didn't know when the visit was* — both are real findings about the source, not formatting problems to be edited around. Regenerating the session's reply is legitimate; hand-editing the payload to pass the screen is not.
3. **Generate the delta review from survivors only**, and state the block count in it so an all-green review can't be mistaken for a full batch.
4. **Report blocks per session**, so an empty batch is visibly empty rather than silently small.

Two corollaries worth stating outright, because both were violated in the incident:

- **A refusal is a successful outcome of the source session, not a failed one.** It means no visit was discussed. The correct disposition is "unchanged — no visit content," with the reason recorded and the chart untouched. If the visit genuinely occurred, its note exists only in the EHR and the gap is real; surface it as a gap rather than papering it with a placeholder entry.
- **Blocking must survive a re-run.** After remediating a bad merge, quarantine the offending payloads — leaving them in the merge queue lets a later session or a resumed run reinstate exactly what was just removed.

### The shape guard, and what building it taught

Item-type validation arrived late, after the same defect family had landed three times. Two findings from that build are worth carrying.

**The tools written to protect the schema mis-read the schema.** The first draft of both the screen and the repair helper classified a string array as an array of objects. The fixture caught it on its first run. A validator is code like any other, and it needs its own tests against the schema it claims to enforce.

**The shipped synthetic fixture was itself invalid** — the test chart carried the exact shape defect the new guard exists to catch. A fixture nobody validates is a second copy of the bug, and it quietly teaches the guard that wrong is normal.

The repair path deserves as much design as the guard. A single-field chart edit tool is legitimate here: the merge already wrote bad history, and refusing the edit leaves it in place. Four requirements make it safe. It must be **serializer-preserving** — same indent, same unicode handling, same trailing newline — so the diff is the one field and nothing else. Dry-run by default. Byte-exact backup before it writes. And it refuses a shape-invalid result rather than coercing one, which is Gate 14b applied to the tool's own output.

State its identity posture out loud. The merge tool has a source document behind it and an identity-gate PASS; a hand-invoked field edit has neither, so the target is operator-asserted. Print a masked target-identity line on every run and say plainly that the operator is the only identity check standing. That is Gate 5's wrong-chart rule restated for a tool that cannot run the rail.

**A fixture that is not wired into the test runner's list runs nowhere.** The build that added this guard went from 13 to 17 test files, 13/13 PASS before and 17/17 after. The rising count is the wiring proof — a green run over a fixture the runner never loaded proves nothing at all.

When you implement a screen like this, **validate it against the incident's own payloads** — the strongest available test set, since those are the exact artifacts that defeated a human review. Include a **positive control** (the real-content payload, defect corrected, must PASS — proving the screen doesn't simply block everything) and a **negative control** (fluent, plausible, content-free prose containing *no refusal phrase at all* must still block — the case a phrase blacklist misses entirely, and the reason Gate 13 tests positively).

---

## Load-bearing architecture invariants

Settled design decisions. Do not relitigate without new evidence; do not "improve" around them.

0. **The browser transport is AGENT-AGNOSTIC and may not be re-narrowed to one agent.** The launch transport must stay runnable identically from every agent in the stack. Canonical = a host-side launcher script attested by **socket ownership** (`lsof` on the dedicated debug port) of a dedicated browser profile. No agent may re-bind this to its own proprietary browser — not in a "hardening" pass, not "temporarily," not for a stated safety reason — without the operator's explicit written per-change sign-off. The real safety requirement is *"never the daily browser" + "verify the BAA account before paste"* — both met by the attested dedicated instance; "must be *my* browser" is single-agent lock-in wearing a safety costume. (History: one agent welded the transport to its own browser in a hardening pass; it was reverted and the agent-agnostic transport proven live from a different agent the next day.)

1. **The capture endgame is a local, deterministic, no-LLM script — a PHI closed circuit.** Capturing bytes from the EHR needs no model at runtime. Swapping in a local LLM to drive the browser would not fix a process-isolation bug, and it would add a reasoning layer to a step that must be deterministic.

2. **Passive capture beats active refetch.** Wrap the EHR's own in-flight `fetch`/XHR responses rather than re-requesting documents. Two incidents: (a) an out-of-context credentialed refetch design 404'd — the view token isn't freely refetchable; (b) "active refetch works" evidence turned out to be a **cache artifact** (identical byte counts on passive and active). Capture at response time, in the page.

3. **The process-isolation wall is real.** The EHR's document PDF viewer opens in a separate browser process; every external DevTools-protocol driver loses control at that instant ("Cannot attach to this target"). **Page-resident code does not hit this wall** — a hand-pasted DevTools console probe captured a real PDF while every automated external driver failed. Do not spend another session trying to attach an external driver to the viewer.

4. **The shipped resolution: a small browser extension** — MV3, `world:"MAIN"` `document_start` content script wrapping the page's own fetch/XHR (passive, primary), writing each captured PDF straight to the mounted Drive via the File System Access API. Semi-manual by design: the clinician opens each document, it auto-saves — no pasting, no tokens, no LLM at runtime.

5. **Capture → Drive → then the scribe, in that order.** Intake writes everything to the Drive *before* assembling the scribe session, so a scribe failure never costs the captured chart.

6. **The structured chart.json is the source of truth.** Never fall back to legacy loose-summary files. An established patient without a valid chart.json → `NEEDS_BACKFILL`, excluded from launch unless the clinician explicitly accepts a source-chat-only rescue.

7. **Use the canonical scripts as-is — never hand-roll builder/writer logic.** Evidence: a run that hand-rolled its own capture writer produced a malformed `.sha256` sidecar (bare hash — `shasum -c` falsely fails) and scrambled role labels in the saved thread. Deterministic, tested scripts only.

8. **A dismissed side-signal can be the canary.** A count-API 401 that was waved off as "accepted-unavailable" shared the failing auth path that was silently corrupting document retrieval (the Gate-6 incident). When you accept a degraded signal, write down what it shares with the signals you still trust — and re-examine it the moment anything downstream looks odd.

---

## If a gate blocks you — the required behavior

1. **Stop at the gate.** Do not construct an alternate path, a "temporary" bypass, or a cleverer verification that substitutes for the gate. Every gate above survived at least one reviewer smarter than the situation you're in — the app-shell false PASS passed a manifest, a red-team, AND a frontier-model review.
2. **Report precisely:** which step, which surface was active, the exact error/status, and whether any file was or wasn't written to the Drive.
3. **Bucket, don't force:** the status buckets exist so an honest partial result beats a forced complete-looking one.
4. **Outputs from a bypassed gate do not count.** A capture from the daily browser, a save without content-validation, a merge without delta review — these must never drive a chart update, an archive, or a PASS claim, even if they "look fine."

---

## Documentation patterns worth stealing

- **Every gate cites its incident.** A rule with its origin story survives "surely this doesn't apply here"; a bare rule doesn't.
- **Date-stamp volatile facts** and keep them in their own section, separate from the invariants — with re-verification commands so a future session can check them instead of trusting them.
- **If this skill and the live command file ever disagree, the live command file wins** — fix the skill to match and note the date. Mirrors serve sources, never the reverse.
