---
description: Check every file that restates your canonical rules against the canonical source and re-sync any that drifted. Date-marker based - cheap to run, catches drift before an agent acts on a stale copy.
---

# /sync-mirrors — keep rule mirrors in lockstep

Your canonical rules live in ONE file (here: `rules/canonical-rules.md`). Several other files restate or encode them so that agents which never read the canonical file still get the rules — a peer agent auto-loads its own instruction file, external chat tools get a paste-in seed prompt, skills embed rule subsets. Those copies drift. This command detects drift and re-syncs.

**Why this matters in a multi-agent setup:** every agent reads a *different* entry-point file. A rule updated only in the canonical source silently leaves every other agent running the old rule. Drift isn't a cosmetic problem — it's an agent taking a real action under a retired rule.

## When to run

- Immediately after editing the canonical rules file.
- At session start if it's been a while and you're unsure the mirrors are current.
- Any time `[STALE]` shows up in the check below.

## The design

**Each tracked file carries a hidden marker:** `<!-- rules-sync: canonical-rules.md@YYYY-MM-DD -->`. The marker date is the canonical file's `date_modified` it was last synced to. Comparing marker dates to the canonical date is a one-pass, no-LLM-judgment drift check.

**Tiers matter.** Not every mirror should carry all rules:

| Tier | What it mirrors | Obligation when canonical changes |
|---|---|---|
| A | Full rule block, **verbatim** (agent entry-point files like `CLAUDE.md` / `AGENTS.md`) | Re-mirror the whole block exactly. Don't renumber — rule slots are anchors even when a rule is retired. |
| B | A **relevant subset** (a seed prompt only needs content rules, not process rules; a skill only needs the rules it enforces) | Read the canonical diff and judge relevance; update only if a rule in this file's subset changed. |

**Not tracked, by design:** files converted to *pointers* at the canonical source carry no restated rule text and cannot drift. The fix for a drift-prone restatement is to pointer-ize it, not to track more copies.

## Step 1 — Detect drift

```bash
CANON="rules/canonical-rules.md"
canon_date=$(grep -m1 '^date_modified:' "$CANON" | sed 's/.*: *//' | tr -d ' ')
echo "Canonical $CANON date_modified: $canon_date"
drift=0
while IFS=: read -r file tier; do
  marker=$(grep -o 'rules-sync: canonical-rules.md@[0-9-]*' "$file" 2>/dev/null | head -1 | sed 's/.*@//')
  if [ -z "$marker" ]; then
    printf '[NO MARKER] (tier %s) %s — add a marker\n' "$tier" "$file"; drift=1
  elif [ "$marker" = "$canon_date" ]; then
    printf '[OK]    (tier %s) %s @ %s\n' "$tier" "$file" "$marker"
  else
    printf '[STALE] (tier %s) %s @ %s  ->  canonical %s\n' "$tier" "$file" "$marker" "$canon_date"; drift=1
  fi
done < mirrors.list   # lines of  path:tier
[ "$drift" = 0 ] && echo "All mirrors in sync." || echo "Drift detected — proceed to Step 2."
```

## Step 2 — Re-sync anything flagged

For each `[STALE]` / `[NO MARKER]` file:

1. **Read** the current canonical text and the flagged file.
2. **Tier A** — replace the rule block with current canonical rules, preserving each file's surrounding framing.
3. **Tier B** — read the canonical diff, judge whether it touches this file's subset, update only what's relevant. Never leave a detailed restatement half-updated without an in-file note saying which parts were verified.
4. **Show the operator the proposed change before writing** if it touches rule wording — rules are the one text class where a silent "improvement" is a bug.

## Step 3 — Bump the marker

After re-syncing a file, update its marker to the canonical date (via a reviewable edit, not sed). Re-run Step 1 to confirm everything reads `[OK]`.

## Honest limitation

This tracks **staleness by date**, not semantic equivalence — `[OK]` means "synced to the current canonical date," not "a human re-verified every word." If you hand-edit the canonical file, bump its `date_modified`, or the mirrors will read `[OK]` while actually stale. Cheap-and-honest beats thorough-and-never-run.
