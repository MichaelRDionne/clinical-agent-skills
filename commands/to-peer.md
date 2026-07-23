---
description: Compose, safety-gate, and file a de-identified handoff to a peer coding agent (e.g., Codex) in a shared file channel. ASYNC — the peer reads it when it's next running; this does NOT wake the peer or make it respond.
---

# /to-peer — file a handoff to a peer agent

Compose a handoff from this agent to a peer agent (another CLI coding agent with access to the same working directory) per the green-light protocol. `$ARGUMENTS` = the topic/intent and any specifics (e.g. `/to-peer re-run phase-2 verification on the open worklist`).

> **What this is:** a composer that writes a properly-named, de-identified, safety-scanned handoff file into the shared channel. **What it is NOT:** it does not wake the peer, start a watcher/daemon, poll for replies, or run anything on the peer's behalf. The peer picks the file up when it is running (it may be offline / out of credits — say so if relevant).

## Hard requirements (from the red-team — non-negotiable)

1. **De-identified only.** No PHI, no patient identifiers, no chart/note text, no real auth cookies / stream URLs / document IDs. Structural detail + paths only. Protected data stays on its encrypted volume — it never enters the channel.
2. **Safety gate is BLOCKING.** After writing, run your denylist scanner against the file (a small script that greps for your organization's forbidden terms: identifier patterns like DOB/MRN/SSN, plus any org-specific vocabulary that must never leave internal files). If it reports ANY finding, **STOP — fix the file and re-scan until clean.** Never leave a flagged file in the channel.
3. **Stays GREEN.** Filing a de-identified handoff is a GREEN action under the autonomy protocol (see the `multi-agent-protocol` skill). Do NOT escalate: no daemon, no auto-poll, no auto-execute, no waking the peer.
4. **Restrictive perms** (`chmod 600`) on the file.

## Steps

1. Resolve the topic from `$ARGUMENTS`; make a kebab slug.
2. Get the REAL date: `date +%Y-%m-%d` (don't use a remembered date — drafter dates are unreliable).
3. Write `collab/handoffs/<DATE>-<this-agent>-to-<peer>-<slug>.md` with frontmatter:
   ```
   ---
   title: <ThisAgent> to <Peer> — <Topic> - <DATE>
   tags: [ai-collaboration, handoff]
   status: Active
   date_created: <DATE>
   source: <this-agent>
   ---
   ```
4. Body sections: **Purpose** · **What the peer should do** · **Acceptance / gate criteria** (if applicable) · **Report back as** `<peer>-to-<this-agent>-<slug>.md` · **Data Pre-Flight** (one line affirming de-identified, structural-only).
5. `chmod 600` the file.
6. Run the **blocking safety scan** (requirement #2). Fix + re-scan until it reports no findings.
7. Append the thread to the LIVE section of `collab/handoffs/THREAD-STATUS.md` (don't rename/move existing watched files — that breaks the watcher baseline).
8. Report back to the operator: the file path, the clean-scan confirmation, whether the peer is currently running, and the one-line prompt they can paste into the peer to pick it up:
   `Pick up and execute: collab/handoffs/<DATE>-...-<slug>.md — report back as <peer>-to-<this-agent>-<slug>.md`

## Why the design is shaped this way

- **Async file channel, not IPC:** files are inspectable, diffable, and survive either agent crashing. A daemon that auto-executes peer requests is the single biggest autonomy-creep risk in a two-agent setup — this design makes it structurally impossible.
- **The scan runs on every handoff, every time,** even when "it's obviously clean." The one time it isn't obvious is the time that matters.

## Companion

- `/from-peer` — the read/review direction. Reading the peer's reply is a separate, deliberate step — never automatic.
