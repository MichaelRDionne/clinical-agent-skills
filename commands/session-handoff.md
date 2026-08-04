---
description: Session close-out for agent sessions with live knowledge-base access - pre-flight rule scan, an independent audit of the session by a second agent, human review gate, then drop the entry unnumbered into a filing basket. The session log is what makes multi-session agent work coherent.
---

# /session-handoff — close out an agent session

Use this at the end of any working session to file a dated session-log entry. The session log is the backbone of long-running agent collaboration: the most recent entry IS the current state of work, and every agent (or future session) grounds itself by reading it. A session that ends without an entry is a session the next agent can't see.

> **Sessions no longer assign their own numbers.** The approved entry is dropped **unnumbered** into a filing basket (`inbox/session-drafts/`) with `session: UNFILED` and a `drafted_at` timestamp. A single serializing filer script — run as step zero of the next session kickoff — assigns numbers in `drafted_at` order, renames the entry and its staged attachments, and moves them into `session-log/`.
>
> The reason is concurrency. When several sessions run at once, every one of them reads the same "highest number so far" and every one of them claims the next integer. One writer, running at a moment when no session is drafting, cannot collide with itself. Everything below is written for that model; if you only ever run one session at a time, the older claim-a-number-at-close approach still works and the rest of this file applies unchanged.
>
> Pick a **draft base** early — `DRAFT_BASE = YYYY-MM-DD-<kebab-topic>`. It names the draft file, its staged attachments (`<DRAFT_BASE>--<slug>.<ext>`), and the audit report below. Wanting a number before the filer runs is itself the bug.

## Step 1 — Read live context

In parallel:
- Read the canonical rules file (always — even when the drafting tool "should have" applied them; the pre-flight catches what it missed).
- List the recent ~20 files in `session-log/` to detect continuation candidates, and confirm the filing basket is empty. **A non-empty basket means an earlier session's draft was never filed, and it is newer than anything in `session-log/`** — anyone grounding on "the most recent entry" without checking the basket is grounding on stale state.

## Step 1b — Launch an independent audit of the session

**Every close-out gets an audit pass over the whole session by a second agent, before the entry is written.** Dispatch it in the background and keep working through the steps below; collect the findings at the review gate.

**Do not write the auditor's input yourself.** A digest composed by the agent under audit filters out precisely the errors the audit exists to catch. The auditor reads the session transcript, flattened by a deterministic script with no model in the loop:

```bash
SD="<this session's scratchpad dir>"
TX="<transcript dir>/$(basename "$(dirname "$SD")").jsonl"   # UUID comes from the scratchpad path
cp "$TX" "$SD/session-raw.jsonl"        # snapshot — the live file is still being appended to
python3 <your-extractor>.py "$SD/session-raw.jsonl" "$SD/session-audit-digest.md"
chmod 600 "$SD/session-raw.jsonl" "$SD/session-audit-digest.md"   # transcript copies, never world-readable
```

The extractor is not shipped here — write your own against whatever your agent's transcript format is. Its contract is short: read the raw session log, emit every user turn and every tool call with its result in order, drop image and base64 payloads, truncate very long blocks with a marker, and make no judgments. Offer a `--full` switch so the auditor can ask for an untruncated re-run. A model anywhere in this step defeats the purpose.

**Derive the transcript path from your own scratchpad path. Never select it by newest mtime.** Under concurrency that is a coin flip: on one verified run, the newest-mtime transcript at audit time belonged to a *different* concurrent session, **9 seconds newer**. A compliant auditor following a "find the most recently modified transcript" instruction audits the wrong session and returns entirely plausible findings about it. Five transcripts were touched inside three minutes on that machine.

**Hard gate — the dispatch prompt may not be composed until all three hold:**

1. `test -s "$SD/session-audit-digest.md" && echo DIGEST-OK` printed `DIGEST-OK`. Run it and see the receipt **before writing one word of the dispatch prompt**.
2. The dispatch prompt carries the digest's **literal absolute path**, pasted from that receipt — never a description of how to find one.
3. The dispatch prompt contains **no transcript-selection procedure at all.** "Most recently modified", "newest", "latest", and any mtime or glob hunt are banned dispatch text.

The ordering carries a real dependency. A dispatch composed before the digest exists has nothing to point at, so it degenerates into exactly the two banned inputs: a self-authored summary of the session plus a find-it-yourself transcript hunt. That is what happened the first time — a seven-item "what this session did" self-characterization, launched ahead of the digest. It was caught in review that time. This gate exists so the next one doesn't depend on being caught.

Give the auditor a self-contained prompt: it never replays your conversation. Restate the firewall rules inline, make it **report-only** in the knowledge base, and require it to write its full findings to a file outside the knowledge base before returning — a returned summary can be truncated, a written report can't. Address the findings to the operator, not to the agent that dispatched it.

**Pick the auditor's tier by what the session touched**, and name the tier you used in the review gate. A cheap model is adequate for re-verifying receipts and counts. Reserve your strongest model for sessions that drafted outbound copy, ran a delegation flow, or touched regulated data — relay fidelity, invented biography, and judgment calls are what the cheap tier misses.

## Step 2 — Pre-flight scan

Scan the draft entry against your organization's rules (forbidden vocabulary, protected data, actions that need approval). Maintain an explicit **carve-out list** — known-legitimate patterns that would otherwise false-positive — and do NOT flag those. A pre-flight that cries wolf gets skipped; the carve-out list is what keeps it credible.

Surface real violations in a FLAGS block. Never silently rewrite.

## Step 3 — Name the draft (no number)

The draft is named `<DRAFT_BASE>.md` = `YYYY-MM-DD-<kebab-topic>.md`, and it declares `session: UNFILED` plus `drafted_at: <ISO timestamp>`. The filer turns that into `YYYY-MM-DD-S<n>-<kebab-topic>.md` on its next run. Session numbers still increment monotonically across days, and multiple sessions per day are still fine — the increment just happens in one place.

Three patterns survive the change. Each becomes a note the filer reads:

1. **Continuation** — the draft elaborates on already-filed content. Record `continues: S<parent>` in the frontmatter; the filer emits `YYYY-MM-DD-S<next>-s<parent>-continuation-<topic>.md`. (An "addendum to the newest entry" convention was retired earlier: it proved impossible to validate mechanically, because every addendum form broke the "unique highest session ID" check. If a naming convention can't pass its own validator, retire the convention, not the validator.)
2. **Backfill** — the work is dated earlier than the newest filed session. Keep the **original event date** in `DRAFT_BASE`, add a provenance note in the entry, and let the filer assign the next number anyway. Preserve time-locked facts verbatim.
3. **Standard new session** — today's date, no number.

**Do not stamp a session number on anything at authoring time** — not filenames, not attachment slugs, not report artifacts, not links between entries. The number does not exist until the filer runs. Reaching for one mid-session is the signal that something is about to be misfiled.

### If you enforce that rule with a script, mind the allowlist

Filename and frontmatter checks miss the case that actually bites: a free-text `S<n>` anchor written into the *body* of a tracker or wiki page. In the originating setup, four such mis-stamps landed in three days after the filename gates shipped, so the body scan became a required close-out receipt.

A body scan immediately hits a legitimate exception. Some anchors point at numbers a session claimed and then never filed — the number is spent, no entry will ever exist, and the reference is correct history. Those produce a red that can never be cleared, and a permanent red is one a reader learns to skip. The fix is a small registry of claimed-but-never-filed numbers that the checker subtracts. Three properties make it safe, and all three were bought the hard way:

1. **Fail closed in both directions.** A malformed registry line is a hard error with its own exit code, never a skipped line. A *missing* registry file means an empty registry — strictly more red, never less. An allowlist whose absence quietly suppresses alerts is worse than no allowlist.
2. **Never add an entry to silence a red you are currently looking at.** Additions require independent evidence that the number was really claimed and really never filed. Skip this and the registry degrades into a mute button, which is the failure mode every suppression list converges on unless the rule is written down next to the list.
3. **Keep the registry outside the checker's own inputs.** If the checker derives "already filed" from a directory listing, the registry file must not appear in that listing — a dotfile, or a path outside the scanned tree. Otherwise the fix feeds itself.

One more, from watching the change nearly undo itself: the first draft of the registry patch carried a test stamp written in the same form as a real anchor, which would have re-created the exact permanent red the change was retiring. Write self-test fixtures so they cannot be mistaken for the thing they test — assemble the literal from pieces at runtime, so the pattern exists only while the test runs.

## Step 4 — Documents → summarize + attach

For every document surfaced, pasted, fetched, or produced this session: write a 1–3 sentence summary in the entry's **Attachments** block, and stage the **full document intact** alongside the draft as `<DRAFT_BASE>--<kebab-slug>.<ext>`. The filer renames it to `S<n>-<kebab-slug>.<ext>` and moves it into `session-log/_attachments/` with the entry. Do not truncate or reformat the staged copy — it is the archival original.

## Step 5 — Memory delta check

Before drafting the entry, ask: *did a durable fact, preference, decision, or workstream state change this session?*
- **Yes** → stage the one-line memory addition for the review gate; apply after approval.
- **No** → state "no memory delta" in the entry. **The negative declaration is required — silence isn't an answer.** (This one rule is what keeps a shared-memory file trustworthy: an absent line is ambiguous, an explicit "no delta" is information.)

## Step 6 — Task-register delta

Inspect the live task register against this session's actual work and declare one of:
- `Task register: <N> closed / <M> added / reconciled through <DRAFT_BASE>.`
- `Task register: no delta / reconciled through <DRAFT_BASE>.`

A no-delta declaration still requires actually checking. Apply the register update only AFTER the draft exists (Step 8), then run your register-consistency check script — a written entry plus a red check is an incomplete handoff.

## Step 6a — Collect the audit

Retrieve the auditor's report from Step 1b and read it in full. In the review gate, state the tier you dispatched, the report's path, and every finding — including the ones that fault your own work this session. Where you disagree with a finding, hand the operator the finding and your disagreement side by side, and let them settle it.

An audit that is launched and never collected is worse than no audit: it produces the paperwork of a check without the check.

## Step 7 — Review gate

Show the operator: proposed `DRAFT_BASE`, pre-flight result (clean OR each violation with its rule), the audit findings and auditor tier, the staged attachment list, and the exact staged memory delta or "none." **Wait for explicit approval.** The handoff writes history — history gets a human gate.

## Step 8 — Write to the basket

On approval, write the entry and its staged attachments into the filing basket. Do not write into `session-log/` — the filer owns that directory, and a second writer is how numbering collides.

## Entry format

    ---
    title: <topic>
    tags: [session-log, <relevant-tags>]
    date_created: YYYY-MM-DD
    drafted_at: YYYY-MM-DDTHH:MM:SS
    source: <agent-name>
    session: UNFILED
    ---

    # <topic>

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

    ## Audit
    - [Auditor tier, report path, findings. Or "Audit clean."]

## The transferable pattern

Seven ideas that survive any domain:

1. **Monotonic session numbers give every piece of work a stable address** — but under concurrency, only one writer may mint them, and it must run when nothing else is drafting.
2. **A pre-flight with an explicit carve-out list stays credible.** One that cries wolf gets skipped.
3. **Attachments are archived intact, never paraphrased.**
4. **Negative declarations are mandatory.** "No memory delta" and "no task delta" are information; silence is not an answer.
5. **The human gate sits exactly where history gets written**, and nowhere else it would slow work down.
6. **The agent under audit does not write the auditor's input.** Flatten the raw transcript with a deterministic script, hand over its literal path, and ban every "go find the latest one" instruction — under concurrency those resolve to somebody else's session.
7. **Order the steps that have a dependency, and say why.** Build the digest, see its receipt, *then* compose the dispatch. Written as a preference it gets reordered by whichever agent is in a hurry; written as a gate with the receipt in between, it doesn't.
