---
description: Start a working session in your knowledge base — read context, check for stale state, propose today's top priority.
---

# /kickoff — session start

Run at the beginning of every working session. Loads context, surfaces what's outstanding, proposes a top priority for the operator to confirm or correct.

## Instructions for the model

Do these steps in order. Use parallel tool calls where independent (steps 1–4 can all run together — but Step 0 runs strictly first).

### Step 0 — File any pending session drafts

Run your session-filing script here. This is the "step zero of the next session kickoff" that `/session-handoff` describes: sessions don't assign their own numbers at close-out, they drop finished, unnumbered entries into a filing basket, and the next session to start files them — assigning numbers in `drafted_at` order, renaming entries and their staged attachments, moving them into your session-log directory, and advancing the register marker. An empty basket is a normal no-op.

This command doesn't ship that filer — write your own against your own session-entry format (see `/session-handoff`'s contract for the shape it expects), or inline the three operations if you're not running the drafts-basket pattern at all.

**This must run before Step 2 and before the task-register gate** — until the basket is drained, "most recent session-log entry" and the freshness check below are both blind to any work sitting in it. Skipping this step on a non-empty basket means grounding today's session on stale state.

Report its receipt lines in the kickoff message, or "no drafts pending." Give your filer distinct exit codes for the two failure shapes that matter: one for "a draft was skipped as malformed" (report it; the draft stays in the basket until fixed) and one for "hard error, filing halted mid-basket" (stop, report, and do **not** proceed to the task-register gate — a partially drained basket means the gate is still blind to the unfiled remainder).

### Step 1 — Load core context

Read these in parallel:
- Your root agent-instructions file (`CLAUDE.md`, `AGENTS.md`, or whatever your tool reads automatically) — operating manual + structural rules.
- Your canonical rules file — the hard constraints that override default behavior.
- Your operational/standing-rules file (skim, don't fully internalize unless relevant to today).

### Step 2 — Check recent state

In parallel:
- List your session-log directory and read the **most recent dated entry**. This tells you what was worked on last and what state things were left in.
- List your inbox/triage folder. If anything is there, note the filenames — they're candidates for triage this session.

### Step 3 — Surface live blockers (skim)

Glance at these only to catch anything that has a deadline this week:
- Your live task register — authoritative for the active priority list.
- Your compliance/deadline tracker, if you keep one — regulatory renewals, license deadlines, insurance dates, whatever recurring deadlines carry real cost if missed.

Don't read these in full unless something is clearly time-bound.

> [!warning] Watch for stale planning snapshots
> If an older point-in-time planning document exists from before your task register became the authoritative source, don't ground on it by accident — a stale snapshot can keep recommending work that's already been superseded, deprioritized, or shelved. Your live task register wins on any conflict.

**Task-register gate (mechanical and blocking — run it, don't eyeball it):**

Run a small, deterministic check here — not a model judgment call. The contract: key it to a "reconciled as of session N"-style marker, not the calendar date, so a later same-day session can't pass silently against a stale marker. Have it return one code for CURRENT, a different one for STALE, and a third for invalid/missing/future state.

This command doesn't ship that script either — it's a few lines against your own register's frontmatter, not something worth vendoring.

On **STALE** or **ERROR**: report the exact state, do **not** propose a priority or begin task work, and ask the operator for one explicit choice: reconcile the register now, or override this kickoff once. An override is only for that kickoff; it does not clear the gate. Never replace the check with a date comparison, and never rationalize past its nonzero exit.

### Step 4 — Propose today's priority

Only run this step after the task-register gate reports CURRENT, or after the operator explicitly grants a one-kickoff override.

Output a brief kickoff message in this format:

```
## Kickoff — [today's date]

**Last session:** [one-line summary of the most recent session-log entry — what shipped, what shifted]

**Open inbox items:** [count and one-line description, or "none"]

**Imminent deadlines:** [anything time-bound this week, or "none flagged"]

**Proposed priority:** [one or two sentences naming the highest-leverage thing to do today and why]

**Alternatives if you'd rather:** [1–2 alternative directions, briefly]

What's the call?
```

### Rules

- Don't dump everything you read — the operator already knows what's in the rules files. Reference them only if relevant to today's priority.
- Propose ONE primary priority, not three. Alternatives go in their own line.
- Be specific. "Work on the website" is not a priority — "turn off the payment-plan banner on the pricing page, since it contradicts the cash-only policy" is.
- If the inbox has unsorted items, factor that into the priority calculus — sometimes triage IS the priority.
- If the most recent session-log entry says something is **blocked on X** and X has resolved, surface that as a likely priority candidate.

## Related

- `/session-handoff` (this repo) — the close-out counterpart this command's Step 0 depends on.
- A long-form kickoff prompt for sessions running outside your primary agent tool, if you keep one — same context, written for a human to paste rather than a tool to auto-load.
- Your own inbox-triage command, if you have one, for filing anything sitting in the inbox folder.
