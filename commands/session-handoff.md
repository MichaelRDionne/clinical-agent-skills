---
description: Session close-out for agent sessions with live knowledge-base access - pre-flight rule scan, sequential session numbering, human review gate, then write the dated session-log entry. The session log is what makes multi-session agent work coherent.
---

# /session-handoff — close out an agent session

Use this at the end of any working session to file a dated session-log entry. The session log is the backbone of long-running agent collaboration: the most recent entry IS the current state of work, and every agent (or future session) grounds itself by reading it. A session that ends without an entry is a session the next agent can't see.

## Step 1 — Read live context

In parallel:
- Read the canonical rules file (always — even when the drafting tool "should have" applied them; the pre-flight catches what it missed).
- List the recent ~20 files in `session-log/` to determine the max session number and detect continuation candidates.

## Step 2 — Pre-flight scan

Scan the draft entry against your organization's rules (forbidden vocabulary, protected data, actions that need approval). Maintain an explicit **carve-out list** — known-legitimate patterns that would otherwise false-positive — and do NOT flag those. A pre-flight that cries wolf gets skipped; the carve-out list is what keeps it credible.

Surface real violations in a FLAGS block. Never silently rewrite.

## Step 3 — Determine session number + filename

Naming convention: `YYYY-MM-DD-S<n>-<kebab-topic>.md`. Session numbers increment monotonically across days; multiple sessions per day are fine. Three patterns, in order:

1. **Continuation** — the draft elaborates on already-filed content → take the **next sequential number** and reference the parent: `YYYY-MM-DD-S<next>-s<parent>-continuation-<topic>.md`, with a "continues S\<parent\>" line at top. (We retired an "addendum to the newest entry" convention after it proved impossible to validate mechanically — every addendum form broke the "unique highest session ID" check. Lesson: if a naming convention can't pass its own validator, retire the convention, not the validator.)
2. **Backfill** — the draft is dated earlier than the newest session → still assign the **next sequential number**, keep the **original event date** in the filename, and add a provenance note in the entry. Preserve time-locked facts verbatim.
3. **Standard new session** — next number, today's date.

```bash
ls session-log/ | grep -oE 'S[0-9]+' | sed 's/S//' | sort -n | tail -1
```

## Step 4 — Documents → summarize + attach

For every document surfaced, pasted, fetched, or produced this session: write a 1–3 sentence summary in the entry's **Attachments** block, and save the **full document intact** to `session-log/_attachments/S<n>-<kebab-slug>.<ext>`. Do not truncate or reformat the attached copy — it is the archival original.

## Step 5 — Memory delta check

Before drafting the entry, ask: *did a durable fact, preference, decision, or workstream state change this session?*
- **Yes** → stage the one-line memory addition for the review gate; apply after approval.
- **No** → state "no memory delta" in the entry. **The negative declaration is required — silence isn't an answer.** (This one rule is what keeps a shared-memory file trustworthy: an absent line is ambiguous, an explicit "no delta" is information.)

## Step 6 — Task-register delta

Inspect the live task register against this session's actual work and declare one of:
- `Task register: <N> closed / <M> added / reconciled through S<n>.`
- `Task register: no delta / reconciled through S<n>.`

A no-delta declaration still requires actually checking. Apply the register update only AFTER the entry exists (Step 8), then run your register-consistency check script — a written entry plus a red check is an incomplete handoff.

## Step 7 — Review gate

Show the operator: proposed filename + session number, pre-flight result (clean OR each violation with its rule), the attachment list, and the exact staged memory delta or "none." **Wait for explicit approval.** The handoff writes history — history gets a human gate.

## Step 8 — Write

On approval, write the entry and attachments.

## Entry format

    ---
    title: Session <n> — <topic>
    tags: [session-log, <relevant-tags>]
    date_created: YYYY-MM-DD
    source: <agent-name>
    session: S<n>
    ---

    # Session <n> — <topic>

    ## What we did this session
    - [3–8 bullets. Past tense. Specific.]

    ## Artifacts
    [Verbatim durable outputs, or "None — exploratory/operational session."]

    ## Attachments
    [Per document: summary + link to archived original. Or "None."]

    ## Open threads / next steps
    - [Unfinished items, blockers, decisions needed]

    ## FLAGS
    - [Pre-flight violations, or "Pre-flight clean."]

## The transferable pattern

Five ideas that survive any domain: (1) monotonic session numbers give every piece of work a stable address; (2) a pre-flight with an explicit carve-out list stays credible; (3) attachments are archived intact, never paraphrased; (4) negative declarations ("no memory delta", "no task delta") are mandatory — silence is not an answer; (5) the human gate sits exactly where history gets written, and nowhere else it would slow work down.
