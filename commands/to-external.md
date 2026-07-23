---
description: Package a task into a self-contained, safety-gated, copy-paste block for an external chat LLM that has NO filesystem access (e.g., Grok, ChatGPT, Gemini in a browser tab). Offloads token-heavy generation to credits you already pay for. Outputs ONE clean START COPY / END COPY block — never sends anything itself.
---

# /to-external — hand a task to a context-less external LLM

Assemble a self-contained prompt the operator can paste into an external chat tool. `$ARGUMENTS` = the task and any specifics (e.g. `/to-external draft 5 opening hooks for the blog post`).

> **Why this exists:** the external tool's subscription credits are already paid for and sit in its app; your primary agent's tokens are the expensive thing. This command moves the *token-heavy generation* (drafts, brainstorms, research, rewrites) to the external tool while the primary agent does only the cheap part — scoping context + safety-gating. If the external vendor bills API and app usage from separate wallets, honor that: the point is to spend the prepaid app credits, not to open a second bill.
>
> **What it is NOT:** it does not send anything, drive a browser, or poll for a reply. It produces a clipboard block. The operator pastes it.

## Token economy (the reason this command exists — honor it)

- **Read the MINIMUM local context needed.** If the primary agent index-hunts 15 files to build the external prompt, it has spent the exact tokens the command is trying to save. Pull only files/excerpts the external tool genuinely can't infer, and inline *excerpts*, not whole files.
- If the task needs **no local context** (generic writing/brainstorm/research), skip context-gathering entirely — go straight to header + ask.
- **Stop rule — when NOT to offload.** If scoping the task would need more than ~2 files / ~200 inlined lines, or requires knowledge-base-wide synthesis, the offload is net-token-negative — the primary agent spends more assembling context than the external tool saves. Keep those local; offload the generation-heavy, low-context tasks.

## Hard requirements (non-negotiable — the block is going OUTBOUND to an external tool)

1. **Safety gate is BLOCKING — and it scans the PAYLOAD, not the header.** Only the parts the agent assembles can leak a violation: the inlined context + the specific ask. The embedded rules **header is trusted rule text** — it deliberately *names* the forbidden terms (the rules forbidding them), so scanning it would false-positive on every run. Write **only the payload** (Context + Request, before the header is prepended) to a scratch file and run the denylist scanner on it — rely on the exit code (non-zero = block). ANY finding → **STOP, fix the payload, re-scan until clean**, THEN prepend the trusted header.
2. **No protected data.** No patient identifiers, chart/note text, or real clinical details. Describe patterns, not people.
3. **No org-forbidden vocabulary in the body** — whatever terms your organization's rules ban from public/outbound copy, they don't go in the payload either.
4. **No silent strategy leakage.** The scanner can't catch generic business-sensitive content (pricing strategy, unpublished drafts, negotiation posture). When context includes sensitive material, tell the operator to paste into a **private / data-sharing-off** session — consumer-app defaults may train on it.
5. **Copyable block is CLEAN.** Plain markdown inside the fence — no `> ` blockquote prefixes, no commentary, no labels. Use a **4-backtick outer fence** if the embedded template itself contains triple-backtick fences. START COPY / END COPY marker lines sit OUTSIDE the fence so they're never copied by accident.

## Steps

1. Resolve the task from `$ARGUMENTS`. If it's ambiguous enough that the external tool would guess wrong, ask the operator ONE clarifying question — lead with your recommended reading — otherwise proceed.
2. Scope context tightly (see Token economy). Apply the stop rule — if it's too context-heavy to be worth it, say so and keep it local.
3. Assemble the **payload** first, gate it, THEN prepend the trusted header:
   - **Context** (only if gathered) — a `## Context you can't see` section with the inlined excerpts.
   - **The request** — the specific ask, made concrete.
   - **Return format** — instruct the tool to open its output with minimal frontmatter (`source_tool`, `date`, `topic`, `intended_destination`) and suggest a `YYYY-MM-DD-<tool>-<topic>.md` filename, so the reply drops straight into your inbox folder and integrates via your triage command.
   - **Safety gate on the payload** (requirement #1): write it to scratch, scan by exit code, fix + re-scan until clean.
   - **Then prepend the trusted header** — your standing identity/voice/rules block for external tools (kept verbatim; it is load-bearing) — plus any tool-specific tail (e.g., "cite claims with verifiable URLs; don't fabricate DOIs or links — mark unverifiable ones [URL TBD]").
4. Present the result as exactly ONE fenced block between `⬇️⬇️⬇️ START COPY ⬇️⬇️⬇️` and `⬆️⬆️⬆️ END COPY ⬆️⬆️⬆️` marker lines (markers OUTSIDE the fence).
5. Tell the operator the **return path** in one line: paste the tool's answer into the inbox folder, then run the triage command to file it.

## The transferable pattern

Three ideas worth stealing even if your stack differs:

- **Payload/header split for scanning.** Rule text that *names* forbidden terms will always false-positive a naive scan. Scan what you wrote, not what you quote.
- **The stop rule.** An offload command that doesn't know when offloading is net-negative will happily burn more than it saves.
- **A structured return path.** An external tool's output that lands as a formatted file in a triage lane gets integrated; one that lands as a chat blob gets lost.
