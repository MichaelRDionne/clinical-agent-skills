---
description: Open-thread census — sweep your session-log corpus since the last census for work recorded open and never closed. Run every couple of months, or whenever your automation/gap-review command flags staleness.
---

# /thread-census — open-thread census of the session-log corpus

Purpose: find work **recorded as open and never closed** that your live task register was never eligible to see — because it was noted in a session log's own "open threads" section and nothing ever routed it onto the register. Proven ROI: an early run of this census recovered a real, dollar-value financial follow-up that no live tracker had captured — pure upside, and it only exists because a session log is a durable record even when nothing reads it back.

## Step 0 — scope

- Find the previous census: grep your session-log directory for `census` / `sweep` entries; the newest one's coverage end-date is this run's **floor**.
- Scope = floor → today. Record the new floor in the output so the next census can chain. Include any unfiled drafts sitting in your filing basket (see `/session-handoff`) in the corpus — they record open/owed work same as a filed entry, just not yet numbered.
- Number-scoped sweeps are blind by construction to files carrying no entry number. Keep a small allowlist of known-covered unnumbered files with a count; assert with a one-line shell check against your own naming pattern that the set has not grown. Any count above the allowlist forces a date-scoped catch-up for the new files before the run proceeds; legitimate allowlist growth updates the count and says so in the output.

## Step 1 — parallel sweep

One agent per stretch of logs (a month's worth is a reasonable unit), each answering exactly one question: **what does this file record as open, owed, blocked, or deferred that no later file closes?** Extract every "flags" and "open threads / next steps" section verbatim — don't summarize it away.

**The known trap has two halves, and conflating them is the trap:**

- **BOUND the sweep by entry number**, not by date. Floor = the previous census's highest number + 1. Under deferred filing, an entry is numbered when it is *filed*, not when it is *worked* — so a late-filed-but-early-dated entry is routine, and a date-bounded sweep has to adjudicate every one of those on the fly. A number-bounded sweep never has the question; chaining floor→floor by number is the only way nothing is missed or double-counted across runs.
- **ORDER the files by filename date within the sweep.** Entry numbers are **not chronological** under deferred filing, so "does a later file close this?" is only meaningful against calendar order. Sorting the *reading* order by entry number will make you call an obligation open that a later-dated, lower-numbered entry already closed.

Cross-check the two at Step 0 and record any disagreement in the output.

**Corpus size decides the force structure.** The parallel-agent fan-out is a token-budget device for a large corpus. Under roughly 60 entries, read the logs directly — agent summaries drop the literal "flags" / "open threads" text that reconciliation runs against, so delegation costs fidelity and buys nothing at that scale. Whichever you choose, **declare it in the output**.

## Step 1b — enumerate inbox checkpoints

The census oracle has been session-log-only: obligations living in inbox checkpoint files are invisible to it, and one run's only genuine recoveries came from checkpoints reached by luck — a blind spot that self-heals by luck is a blind spot. Run one `ls` over your inbox's checkpoint files (a `CHECKPOINT-*.md` pattern is a fine example); reconcile each against the live register by content anchor — not filename, not whether a session log mentions it. A checkpoint whose own header says a resuming session has nothing to execute is closed; one carrying live pending decisions the register lacks is a recovery.

## Step 2 — reconcile, with the known failure modes in view

Check each candidate against your live task register and later session logs before calling it dropped:

- **"Touched ≠ complete"** — a core finding of this census pattern: a register's "reconciled as of session N" marker is an attestation, not a proof. A fresh marker does not mean the item is actually on the register.
- **Verify before alarming:** more than once, the register turned out to be the stale artifact and the session logs were right — confirmed against the operator's live knowledge each time. Anything contradicting the operator's likely knowledge gets asked, not asserted.
- Some work closes **out-of-band by design** — verbally, or off any tracked system entirely. Absence of a written close is not proof it's open — flag it as "no written close found," not "dropped."

## Step 3 — output (durable, or it didn't happen)

- Write recovered items as rows to your live task register, with session provenance.
- Attach the full per-stretch agent reports as durable files alongside your session-log archive — without attachments, a large sweep costs an enormous number of tokens to re-run if anyone ever needs to re-derive it.
- Add/refresh the sweep-provenance block on your task register (new floor, sessions covered).
- Report to the operator: recovered items first, ranked by stake; then "no written close" ambiguities as questions, not verdicts.
