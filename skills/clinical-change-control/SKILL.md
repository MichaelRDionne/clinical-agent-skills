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
- [ ] **2. Verify a genuine Patient Drive mount** — run the mount-sentinel command (Gate 2) and require `MOUNT_OK`. A directory existing at the mount point proves nothing.
- [ ] **3. Confirm an attested isolated browser surface** — a dedicated browser instance with its own profile, attested by inspecting the OS process/socket. Never the clinician's daily browser. Cannot attest → STOP (Gate 3).
- [ ] **4. Confirm the destination is the BAA-covered scribe account** — not the consumer product, not another account. Unclear = stop and stage files on the Drive for manual paste (Gate 4).
- [ ] **5. If running kickoff:** run the synthetic smoke test first (a test patient through the prompt builder). If it fails, stop; do not build real prompts on a broken pipeline.
- [ ] **6. Know your escalation posture:** on ANY gate failure or ambiguity, **stop and report** — which step, which surface was active, exact error, whether anything was written to the Drive. Never improvise an alternate path. **Stopping is a successful outcome; a workaround is not.**
- [ ] **7. PHI containment set:** commit that patient names, schedule rows, chart JSON, source chats, and prompt content will appear ONLY in files on the Drive — never in the knowledge base, scratch files, stdout, or your chat replies. Final reports carry **counts, status buckets, and the output folder path only** (Gate 1).

---

## The gate table

| # | Gate | Rule | Incident behind it | Failure if skipped |
|---|---|---|---|---|
| 1 | **PHI containment** | PHI exists only in the EHR, the scribe session, and the Drive. Never the knowledge base, scratch, stdout, or chat replies. Reports = counts + buckets + folder path only. | Standing hard rule; the in-repo test scaffold's patient-capable folders were deliberately evacuated from the synced knowledge base for exactly this reason. | PHI lands in a synced, unencrypted, multi-agent-readable location — an unrecallable disclosure. |
| 2 | **Mount sentinel before every write batch** | Before EVERY batch of writes: `mount \| grep` the volume AND `test -f` a sentinel file that only exists inside the true encrypted volume. `MOUNT_FAILED` → STOP, no writes. Dir-exists is NOT a mount check. | Red-team finding: if the disk image unmounts mid-run (sleep/disconnect), the mountpoint can persist as an ordinary directory on the boot volume. | Writes land as **unencrypted PHI on the boot disk** while every path string still "works." |
| 3 | **Attested isolated surface — never the daily browser** | All EHR/scribe browser work runs on an attested isolated surface: a dedicated browser **process** with its own user-data-dir, attested via the OS (process command line / socket ownership) — never the clinician's daily browser. Cannot attest → STOP; anything from an unattested surface **does not count**. | Automation driving the daily browser caused screen-blink/focus-steal/mid-keystroke edits during a live patient visit. It **recurred** when an agent's global config default silently preferred the daily-browser backend at a branch point — an agent-side routing bug, structurally impossible in a transport that dials one dedicated port and has no branch. | The clinician's live browser is hijacked mid-visit; captures come from an unverified surface; the run's outputs are untrusted. |
| 4 | **BAA surface verification** | Verify the session is the covered scribe product in the covered account. Consumer product / other account / unclear → stop; leave ready-to-paste files on the Drive and report the folder path. | BAA rides the account login, not the browser profile — so "it's in a browser we control" proves nothing about coverage. | PHI is pasted into a non-BAA surface — same category of harm as Gate 1. |
| 5 | **Wrong-chart guard (before capture)** | Before capturing, confirm the chart open in the browser is the intended patient — verify name + DOB. Mismatch → abort. The capture harness has NO identity check of its own. | Nothing in the capture mechanics knows *whose* chart is open. | Patient B's documents land in Patient A's folder — cross-contamination no downstream count or checksum will ever flag. |
| 6 | **Payload-reality Gate 0** | After ANY capture and before trusting ANY green status: **open ≥1 captured document and confirm it is real clinical content** — not app-shell, marketing, pricing, or error chrome. `status: PASS` is necessary, never sufficient. | The headline incident: manifest PASSED 14 byte-identical app-shell/pricing pages on two independent runs; magic-byte + text-extraction checks passed; manifest review, red-team, and frontier-model review all missed it; a human opening one PDF caught it. | An entire category of source data is **silently omitted while the pipeline reports PASS** — invisible until it matters clinically. |
| 7 | **Content-valid save + same-day capture** | A saved source must be the actual **message thread** — ≥1 clinician turn AND ≥1 assistant turn of patient-specific content. Sidebar/chat-list/UI captures, home/redirect pages, and empty files FAIL. "File exists" ≠ "source saved." Capture and validate **same-day**; never rely on re-opening a saved URL later. Invalid capture → `BLOCKED_BROKEN_SOURCE`, leave the live session OPEN (it is the only remaining copy), surface **immediately with the still-open URL** — not in the final report. | A remediation sweep found 18 blocked patients whose "saved" files were almost all sidebar/UI captures; on re-export, **17 of 18 saved scribe URLs redirected to the home screen with no thread.** Best explanation: the platform ages conversations out (operationally adopted, not formally proven). | The active list gets cleaned up against worthless backups; the platform ages the real source out; the clinical record of the visit is gone. |
| 8 | **Identity quote (before archive or chart update)** | Archiving or a chart update requires a **specific quoted line from the thread** (name / DOB / explicit patient reference) tying the thread to the slug. Weaker basis → `UNMAPPED`; do not archive, do not merge. | Red-team finding: the content-valid check (Gate 7) validates thread *shape*, not *whose* thread it is — a perfectly valid thread filed under the wrong slug passes content + placement checks. | A real visit is written into the **wrong patient's** append-only chart and drives that patient's future summaries. |
| 9 | **OCR spot-check** | After OCR, read the OCR text of **≥2 scanned PDFs against the source images**. `ocrReviewCount: 0` means nothing tripped an auto-flag heuristic — NOT that the OCR is correct. | A confidently-wrong OCR (transposed dose, flipped date) produces clean-looking text with no error signal anywhere. | A wrong dose or date enters the chart silently and reads as fact forever after. |
| 10 | **Delta review before merge — narrative fields carry the weight** | The model-generated chart-update JSON is reviewed BEFORE the merge script runs: show the clinician the delta, with review weight on the **narrative continuity fields** (interval history, visit note, titration summary) — those are what the clinician reads, and the one thing the EHR's live medication administration record (MAR) can't cross-check. Medication fields merge as *advisory continuity, not the prescribing source* — the authoritative multi-provider MAR is reconciled live at read-time, so a med-field error is caught there; med removals/decreases surface as non-blocking diff flags. Never re-merge a session already marked merged (append-only — double-posting is permanent). | Red-team finding: the merge is append-only — a merged change is permanent chart history propagating into every future summary. The tiering decision (narrative = blocking review, meds = advisory flag) came from analyzing which errors the live MAR would and wouldn't catch. | A wrong **narrative** ("what was done last time") misleads the next visit's orientation — and nothing downstream ever cross-checks it. |
| 11 | **Human sign gate** | Captured bundles, OCR output, and scribe-session output are **drafts**. Nothing reaches the clinical chart without the clinician's review and sign-off. The pipeline never autonomously charts. | The design premise of the whole workflow: a workflow with a human sign gate, not an autonomous agent. | The system becomes an unsupervised prescriber's assistant writing to legal medical records. |
| 12 | **Archive-only — NEVER hard-delete** | Cleanup of scribe sessions is archive/hide only. Hard delete is the ONE irreversible action in the workflow and is out of scope for any agent acting on its own judgment. (One narrow, six-condition staged-purge exception exists for pre-staged quarantine folders — staged-first with a manifest, eligible content only, double-keyed same-session approval naming the exact path, read-back with one final yes, sentinel before + verify after, manifest preserved to a deletion-record first.) Archive only after full per-session proof (Gates 7 + 8, chart status, longitudinal rebuild) AND an explicit yes to an archive question asked *after* verification. `UNMAPPED` / `BLOCKED_BROKEN_SOURCE` / ambiguous sessions stay OPEN. | Designed specifically so the workflow is safe on a low-reasoning background model. Combined with Gate 7's source-decay finding, a wrong delete = permanent loss. | The only copy of a clinical source is destroyed by an agent that misjudged a verification — unrecoverable by construction. |

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
