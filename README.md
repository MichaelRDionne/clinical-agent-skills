# clinical-agent-skills

![lint](https://github.com/MichaelRDionne/clinical-agent-skills/actions/workflows/lint.yml/badge.svg)

Battle-tested Claude Code **skills and slash commands** from a real clinical-automation practice — the governance, safety-gate, and workflow patterns that keep LLM agents useful *and* contained when the data is protected health information and the stakes are legal medical records.

Everything here is **pseudonymized from a live production setup** run by a clinician-developer (me): real incidents, real red-team findings, real standing orders — with every identifying noun genericized (the EHR vendor is "a cloud-based EHR," the employer is "the clinic," tools carry generic names). The engineering substance is intact; the identities are not. Fork it, gut it, adapt it.

## Why this exists

Most published agent configs are demos. These are the opposite: every hard gate in this repo was **paid for with a real incident** — a capture pipeline that reported `PASS` twice on 14 copies of a marketing page, a saved-source format that turned out to be worthless when 17 of 18 archived URLs died, an agent that silently drove the operator's live browser mid-patient-visit. The rules carry their origin stories, because a rule with its incident survives "surely this doesn't apply here" and a bare rule doesn't.

## The five load-bearing ideas

These recur across every file and are the actual transferable IP:

1. **Gate ⇄ incident documentation.** Every non-negotiable rule is paired with the failure that created it. See `skills/clinical-change-control` — the format is the product.
2. **Mechanics-green ≠ content-correct — open the payload.** A green exit code, a passing manifest, even a passing red-team review are *necessary, never sufficient*. The only test that catches a silent content failure is opening the artifact and reading it.
3. **GREEN / YELLOW / RED autonomy + the no-daemon fence.** Agents act freely on read/verify/draft, act-and-report on reversible writes, and stop for a human on anything irreversible or outbound — and nothing runs unless a human session is running.
4. **De-identified reporting boundaries.** Agents that touch protected data report **counts, status buckets, and folder paths** — never the content. The data has a closed circuit; the conversation is outside it.
5. **Verify live, not cached.** Portals lie, cached fetches lie, prior-session notes lie, and "the push succeeded" is not "the served content is right." Every claim about live state gets re-checked against the live surface before it's acted on.

## What's inside

### Skills (`skills/<name>/SKILL.md`)

| Skill | What it encodes |
|---|---|
| [`agent-operating-doctrine`](skills/agent-operating-doctrine/SKILL.md) | Nine principles for being a *trusted senior peer* instead of a service desk or a sycophant: honesty over capitulation, proof-not-status, QC-every-output, lead-with-a-recommendation, make-things-easy. |
| [`clinical-change-control`](skills/clinical-change-control/SKILL.md) | The 12 hard gates of a PHI-touching EHR-automation pipeline, each with its incident: mount sentinels, attested browser surfaces, payload-reality checks, identity quotes, archive-only cleanup. |
| [`multi-agent-protocol`](skills/multi-agent-protocol/SKILL.md) | How multiple agents share one working directory safely: tier model, GREEN/YELLOW/RED, the async file-based handoff channel, one-agent-at-a-time, browser-surface boundaries. |
| [`debugging-playbook`](skills/debugging-playbook/SKILL.md) | Symptom → meaning → **discriminating test** → action, one row per incident-backed failure mode. Includes the "dismissed side-signal = canary" rule. |
| [`portfolio-safety-check`](skills/portfolio-safety-check/SKILL.md) | Pre-publish audit for a professional's public GitHub: the employer/vendor/colleague layer that generic secrets scanners miss, git-history leak checks, and the flip-private → genericize → verify-live remediation pattern. (This repo passed its own check before publishing.) |

### Commands (`commands/*.md`)

| Command | What it does |
|---|---|
| [`/to-peer`](commands/to-peer.md) | Compose, safety-gate, and file a de-identified handoff to a peer agent. Async by design — never wakes the peer. |
| [`/from-peer`](commands/from-peer.md) | Read the peer's replies. **Peer text is data, not commands** — every requested action is classified GREEN/YELLOW/RED, never auto-executed. |
| [`/to-external`](commands/to-external.md) | Package a task for a no-filesystem chat LLM: payload-only scanning, a token-economy stop rule, one clean copy-paste block. |
| [`/token-saver`](commands/token-saver.md) | Patch-don't-rewrite editing for long clinical notes: changed sections only, unchanged wording preserved exactly, effort tiered to clinical risk. |
| [`/sync-mirrors`](commands/sync-mirrors.md) | Date-marker drift detection for every file that restates your canonical rules — because each agent reads a different entry-point file. |
| [`/session-handoff`](commands/session-handoff.md) | Session close-out: pre-flight scan, monotonic session numbering, intact attachments, mandatory negative declarations, human review gate. |
| [`/monthly-audit`](commands/monthly-audit.md) | Automation health check (artifacts, not logs — the false-green rule) + a monthly review of which workflows deserve to become skills. |

## Using these

They're standard [Claude Code](https://claude.com/claude-code) skill/command formats:

- **Commands:** copy into your project's `.claude/commands/` → invoke as `/name`.
- **Skills:** copy the folder into `.claude/skills/` → Claude loads them by description match or via the Skill tool.

Both formats key off YAML frontmatter (a skill's `name` must match its parent
directory, and every file needs a non-empty `description` — that's what
Claude matches against). `python3 scripts/lint_frontmatter.py` checks this;
CI runs it on every push so a broken frontmatter block fails loud instead of
just silently never loading.

But **read them as patterns first.** Paths, folder names, and scanner scripts are placeholders for your own; the *shape* — gates with incidents, blocking scans, human sign-off exactly where history gets written — is the part to keep. The prose says "clinician/EHR/PHI" because that's where this was forged; the same structures apply to any agent workflow touching regulated data, production systems, or anything irreversible.

## Provenance and honesty notes

- Pseudonymized, not fictional: incidents, dates-of-lesson, and quoted failure strings are real, lightly edited only to remove identifying context.
- Names of specific vendors, employers, colleagues, and internal file paths have been replaced throughout. If a detail seems oddly generic, that's why.
- No patient data was ever in these files — the no-PHI-in-the-knowledge-base rule is itself Gate 1.

## License

MIT — see [LICENSE](LICENSE). Attribution appreciated, not required.
