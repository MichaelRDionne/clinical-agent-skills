---
name: debugging-playbook
description: >-
  Symptom-to-fix triage for a clinical EHR-automation pipeline, in the format that made
  it work: every symptom routes to what it means, a DISCRIMINATING TEST, and the correct
  action — and every entry is backed by a real incident where the obvious first guess
  was wrong at least once. Load the moment a run shows a failure symptom. The format is
  the transferable part: adapt the table to your own pipeline's incident history.
---

# debugging-playbook — symptom → meaning → discriminating test → action

When a session sees a symptom during a pipeline run, this file routes it. Every entry is backed by a real incident; the discriminating tests exist because the obvious first guess was wrong at least once.

**Prime directive: report, don't paper over.** For every failure, report four things — **(a)** which workflow STEP you were in, **(b)** which browser surface was active, **(c)** the exact error/status string, **(d)** whether any file was or was not written to the protected volume. Never improvise an alternate path around a failed gate.

**Data hygiene while debugging.** The discriminating tests below open real patient documents on the encrypted volume. Run them locally; report only **counts, hash prefixes, byte lengths, and status categories**. Never paste extracted document text, patient names, or chart contents into a chat reply, a knowledge-base file, a scratch file, or a session log.

---

## Step 0 — universal triage (run before anything else)

1. **Which surface?** Positively confirm the active browser surface is the attested isolated one. If you cannot confirm it, treat it as the operator's daily browser and STOP (Gate 3 in `clinical-change-control`).
2. **Is the volume genuinely mounted?** Before trusting any prior write or making a new one:

   ```bash
   mount | grep -q "<mount-point>" && test -f "<mount-point>/.volume-ok-sentinel" \
     && echo MOUNT_OK || echo MOUNT_FAILED
   ```

   `MOUNT_FAILED` → STOP all writes immediately. Directory-exists is NOT a mount check — an unmounted disk image leaves an ordinary directory stub on the boot volume, and writes there land as **unencrypted protected data on local disk**.
3. **Did anything claim green?** If a PASS/saved/OK status is in play, treat it as *mechanics-green*, not *content-correct*, until you have opened the actual payload (row 1). This pipeline's worst incident was a double false-PASS.

---

## The symptom table

| # | Symptom | What it means | Discriminating test | Action |
|---|---------|---------------|---------------------|--------|
| 1 | Capture "succeeds" but documents are identical to each other, or contain marketing/app-shell content | The document fetch silently fell back to the EHR's app-shell/marketing page. Magic-byte + text checks still pass — this produced a manifest `status: PASS` **twice** on 14 byte-identical copies of the vendor's pricing page | Byte-identity + payload-reality check (Detail 1): hash all captured PDFs — all/most identical is damning; then open one and look for clinical signal (patient/DOB/lab/medication terms) vs app-shell text | FAIL the capture. Do not trust the PASS, do not let it drive a chart update or any deletion. The harness now auto-blocks the known fingerprints — but Gate 0 (a human/agent actually opening one payload) stays mandatory |
| 2 | The captured page is a **pricing/upsell page specifically** | Suspect **plan-tier entitlement gating**, not just an auth bug — the account may genuinely lack access. But do not assume: the same symptom has also been a plain retrieval bug | Click the same item **in the app's own UI** (on the isolated surface). Real content opens → code-fixable retrieval bug. Upsell persists in the UI too → entitlement, not code-fixable | Real content → fix the retrieval path. Upsell in UI → stop coding; it's an account/plan issue for the operator. (Live evidence once killed the plan-tier hypothesis exactly this way — the UI click opened a real document) |
| 3 | `"Cannot attach to this target"`, or `Runtime.evaluate` timeouts the instant a PDF viewer opens | **DevTools-protocol / process-isolation wall.** The PDF opens in a separate browser process (out-of-process frame); every external driver loses control at that moment. Not an auth problem, not fixable by switching models | In-page code survives where the driver dies: page-resident timers keep running, and a hand-pasted DevTools console probe captured a real `%PDF-` while every automated external driver failed | Do NOT keep retrying the external driver — this is settled (one investigation proved the dead-end six independent ways). Use page-resident capture: a browser extension wrapping the page's own fetch/XHR, or the console one-paster fallback |
| 4 | A refetch of a discovered document URL **404s** (or 401s) outside the live viewer context | The document's auth token is **view-scoped, not freely refetchable** | Compare in-context vs out-of-context: the same URL that streams `%PDF-` while the viewer is open 404s from anywhere else | Abandon active refetch as primary. **Capture at response time, passively** — arm the in-page hook *before* the click. Beware the cache-artifact trap: "active refetch works" was once an identical-byte-count cache mirage |
| 5 | A saved scribe-conversation URL opens to the **home screen / no thread** | The platform aged the conversation out. Observed: **17 of 18** saved URLs no longer opened to a thread; only the newest survived | Open the URL on the isolated surface: a real thread shows clinician+assistant turns; an aged-out one redirects home | Source is gone — recover the record from the EHR note or at the next visit. Re-bucket OUT of "re-exportable" into terminal **lost-source**. Standing rule: capture the thread same-day and content-validate it; never trust that a URL reopens later |
| 6 | The operator's screen **blinks**, focus is stolen, or edits appear mid-keystroke | The run is driving the operator's **real browser**, not the isolated surface. A window inside their working browser is not isolated (same process/profile). This recurred because one agent's *global config default* silently won over the per-task instruction | Positively identify the surface: the dedicated process with its own profile, or the operator's? If you cannot prove isolation, it's the real browser | **STOP immediately.** Report; do not continue, do not improvise. Anything captured from the real browser **does not count**. Restart on the attested surface |
| 7 | A volume write "succeeded" but Step-0's mount check returns `MOUNT_FAILED` (or was never run) | The disk image may have unmounted mid-run (sleep, disconnect), leaving a same-named plain directory — your "write" may be **unencrypted protected data on local disk** | Run the Step-0 mount+sentinel command. The sentinel file only exists inside the true encrypted volume | ABORT all writes. Report and ask the operator to remount. If a write may have landed on a boot-volume stub, flag it explicitly so the stray plaintext can be found and securely removed — do not silently move on |
| 8 | UI shows N sessions/documents but API enumeration returns fewer (observed extreme: sidebar showed 28, API returned 0) | The enumeration path is broken or scoped differently from the UI — the smaller number is NOT ground truth | Manually count in the UI vs the enumeration output | Report the gap; never assume the smaller number is complete, and never archive/delete on the strength of an enumeration that undercounts the UI |
| 9 | `shasum -c` fails against a `.sha256` sidecar | Known writer defect from a hand-rolled capture path: sidecar written as a **bare hash** instead of `hash␣␣filename` — the content may be fine | `shasum -a 256 <file>` and compare the digest string to the sidecar contents by eye | Digests match → capture intact; fix the sidecar format, don't re-capture. Truly differ → treat the save as unverified: the source session must stay open |
| 10 | Captured thread shows scrambled role labels (all USER turns before any ASSISTANT turn) | Second defect from the same hand-rolled writer: labels emitted out of order. Harmless for a raw archive; **dangerous if a parser trusts the roles** | Open the raw capture and check whether turn *content* alternates sensibly even though labels don't | Keep the raw file (content is the value); never let a downstream parser trust role labels from this writer without verification |
| 11 | Harness aborts at startup with a capability-probe error ("required capabilities are absent") | A startup probe (evaluate / locator / protocol access) failed — the harness refused to start rather than run degraded | Read the probe booleans in the error artifact to see which capability failed | Fix the surface (usually: not actually on the isolated browser) before re-running. **Do not bypass the probe** |
| 12 | Harness guard: "current URL is not a patient chart" | The active tab isn't on a chart URL — commonly the login page, dashboard, or a stale tab | Look at the reported URL | Navigate to the patient chart first, then re-run |
| 13 | Harness guard: "could not uniquely identify the status filter" / "unrecognized option" | The EHR's UI changed (or an unexpected control matched the selector heuristics) — the harness **fails closed** rather than clicking the wrong control | Open the tab in the UI and compare the actual dropdowns to the harness's expected labels | UI drift: update the selector heuristics. Report; don't loosen the guard blindly |

---

## Detail 1 — payload-reality + byte-identity check (the row-1 test, runnable)

Run in the captured-documents directory on the encrypted volume. Report only counts/prefixes.

```bash
# 1. Byte-identity: how many distinct payloads did we actually get?
#    A single dominant hash across all/most files = app-shell fallback until proven otherwise.
shasum -a 256 *.pdf | awk '{print $1}' | sort | uniq -c | sort -rn | head

# 2. PDF magic: a valid capture starts with %PDF- and is >= 1000 bytes.
for f in *.pdf; do printf '%s: %s %s bytes\n' "$f" "$(head -c 5 "$f")" "$(stat -f%z "$f")"; done

# 3. App-shell fingerprint (needs pdftotext): marketing text = NOT a patient document.
pdftotext -f 1 -l 3 "<one-file>.pdf" - | grep -icE "choose the plan|per provider per month|subscription plans|start.?up fees"

# 4. Clinical signal: a real document says patient things.
pdftotext -f 1 -l 3 "<one-file>.pdf" - | grep -icE "patient|date of birth|dob|lab|result|specimen|reference range|assessment|encounter|diagnos|medicat|consent|signed"
```

Read: test 3 > 0 → app-shell, FAIL. Test 4 = 0 on ≥3 docs → no clinical signal, FAIL. Test 1 showing one hash for everything → FAIL regardless of the others. **Gate 0 still applies even when all four pass:** open one PDF with your eyes and confirm real clinical content before any PASS is trusted. Mechanics-green ≠ content-correct.

(Treat any auth token embedded in a captured URL as a live credential — never log or paste it; redact on sight.)

---

## Detail 2 — dismissed side-signal = canary

**If you catch yourself writing off a small anomaly as "accepted/unavailable," stop — it may share a root cause with the thing you're about to trust.**

The incident: during the false-PASS, a document **count API returned 401/404** and was waved off — literally encoded in the harness as `countApi: { status: "unavailable", accepted: true }` — while the manifest went on to report PASS. That dismissed 401/404 **shared the auth path that was corrupting document retrieval**. The side-signal was the canary; nobody listened, and the run double-PASSed on 14 copies of a marketing page.

Rule: before accepting any green status, list the anomalies you dismissed to get there. Any dismissed anomaly touching the same subsystem (auth, network, session) as the main result invalidates your confidence in the green until explained.

---

## Escalation rules

- A gate says STOP → you stop and report. No alternate path, no "just this once."
- Anything irreversible (archiving a source session, merging a chart update, deleting anything) requires content-validity + identity confirmation AND the operator's explicit go-ahead. When a symptom above is active, the answer is automatically "not yet."
- Before re-fighting a battle ("maybe active refetch works now," "maybe the driver can attach this time"), check the project's failure-archaeology record — if it's marked settled, reopening requires **new evidence**, not fresh optimism.

---

## Adapting this format

The table format is the product: **symptom → what it means → discriminating test → action**, one row per *incident-backed* failure mode. Rules for keeping it honest: (1) no row without a real incident behind it; (2) the discriminating test must cheaply separate the competing explanations — that's what makes it worth writing down; (3) date-stamp volatile facts separately from the rows; (4) a wrong runbook is worse than none — when a re-verification disagrees, fix the row before relying on it.
