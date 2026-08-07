---
description: Check every file that restates your canonical rules against the canonical source and re-sync any that drifted. Two markers per file - a canonical date and a commit SHA pinning the content someone actually read - so a mirror edited on its own still flags.
---

# /sync-mirrors — keep rule mirrors in lockstep

Your canonical rules live in ONE file (here: `rules/canonical-rules.md`). Several other files restate or encode them so that agents which never read the canonical file still get the rules — a peer agent auto-loads its own instruction file, external chat tools get a paste-in seed prompt, skills embed rule subsets. Those copies drift. This command detects drift and re-syncs.

**Why this matters in a multi-agent setup:** every agent reads a *different* entry-point file. A rule updated only in the canonical source silently leaves every other agent running the old rule. Drift isn't a cosmetic problem — it's an agent taking a real action under a retired rule.

## When to run

- Immediately after editing the canonical rules file.
- At session start if it's been a while and you're unsure the mirrors are current.
- Any time `[STALE]` shows up in the check below.

## The design

**Each tracked file carries a hidden marker with two fields:**

```
<!-- rules-sync: canonical-rules.md@YYYY-MM-DD verified@YYYY-MM-DD:<short-sha> -->
```

- **`canonical-rules.md@`** — the canonical file's `date_modified` this mirror was last synced to. Drives `[STALE]`.
- **`verified@<date>:<sha>`** — the commit SHA of the exact file content someone last read against canonical and cleared. Drives the content check: `git diff <sha> -- <file>` against the working tree, ignoring the marker line itself. Any other change flags `[EDITED SINCE VERIFY]`. The date is human-readable bookkeeping; **the SHA is the evidence.**

The second field exists because the first one alone missed an entire failure class. A mirror edited *independently* of canonical — someone improving the wording of a rule in `AGENTS.md`, say — leaves the canonical date untouched, so a date-only check reads `[OK]` forever. When the SHA anchor was added to the originating setup, it immediately surfaced **32 such commits** that had accumulated invisibly.

Anchoring on a SHA rather than a second date is also deliberate. Dates are day-granular, so a date window either false-positives on the very commit that writes the stamp, or permanently hides everything else edited that same day. A red-team pass caught that hole after it had already swallowed roughly **70 changed lines across all 7 tracked mirrors on day one**.

**Bump `verified@` only after actually re-reading the file against canonical** — not because a commit looked innocuous in passing. The stamp is a receipt claiming the content was checked, and stamping without reading is the failure mode this field is most exposed to.

**Tiers matter.** Not every mirror should carry all rules:

| Tier | What it mirrors | Obligation when canonical changes |
|---|---|---|
| A | The full rule block (agent entry-point files like `CLAUDE.md` / `AGENTS.md`) | Update **in place, rule by rule**, so substance, status, and numbering match canonical. Don't renumber — rule slots are anchors even when a rule is retired. |
| B | A **relevant subset** (a seed prompt only needs content rules, not process rules; a skill only needs the rules it enforces) | Read the canonical diff and judge relevance; update only if a rule in this file's subset changed. |

> **Tier A used to say "verbatim." That label was wrong and it cost a rule clause.** An entry-point file legitimately differs from canonical: it is a condensed, agent-facing paraphrase, and it carries operational guards canonical does not — narrower phrasings, "don't do X unasked" riders, per-agent context. Overwriting the block with canonical prose deletes those. But "verbatim" also licenses a re-sync by wholesale replacement, and under that label a substance clause in one rule went missing for weeks with nobody noticing.
>
> So the required match is **substance**, which means the check cannot be a text diff. At every re-sync, verify all rules against canonical one at a time, and record which rules carry deliberate additions. A condensed mirror is only safe if that re-verification is actually performed.

**Not tracked, by design:** files converted to *pointers* at the canonical source carry no restated rule text and cannot drift. The fix for a drift-prone restatement is to pointer-ize it, not to track more copies.

## Step 1 — Detect drift

```bash
CANON="rules/canonical-rules.md"
[ -f "$CANON" ] || { echo "!! CHECKER BROKEN: canonical missing at $CANON"; exit 2; }
canon_date=$(grep -m1 '^date_modified:' "$CANON" | sed 's/.*: *//' | tr -d ' ')
[ -n "$canon_date" ] || { echo "!! CHECKER BROKEN: canonical has no date_modified"; exit 2; }
echo "Canonical $CANON date_modified: $canon_date"

git rev-parse --git-dir >/dev/null 2>&1 && git_ok=1 || {
  git_ok=0
  echo "!! GIT LAYER DOWN — no content check ran. Every line below is date-only."
}

drift=0; seen=0
while IFS=: read -r file tier; do
  seen=$((seen+1))
  # Anchor the grep to the WHOLE marker, both fields. An unanchored pattern lets
  # a sentence elsewhere in the file that merely discusses `verified@` be picked
  # up as the marker — these files document the scheme, so that is a live risk.
  marker=$(grep -oE 'rules-sync: canonical-rules\.md@[0-9]{4}-[0-9]{2}-[0-9]{2}( verified@[0-9]{4}-[0-9]{2}-[0-9]{2}:[^ >]+)?' "$file" 2>/dev/null | head -1)
  if [ -z "$marker" ]; then
    printf '[NO MARKER]  (%s) %s — add a marker\n' "$tier" "$file"; drift=1; continue
  fi
  mdate=${marker#*canonical-rules.md@}; mdate=${mdate%% *}
  case "$marker" in *verified@*) sha=${marker##*:} ;; *) sha="" ;; esac

  if [ "$mdate" \> "$(date +%F)" ]; then
    printf '[BAD MARKER] (%s) %s — future date %s disables this file silently\n' "$tier" "$file" "$mdate"; drift=1; continue
  fi
  if [ "$mdate" != "$canon_date" ]; then
    printf '[STALE]      (%s) %s @ %s  ->  canonical %s\n' "$tier" "$file" "$mdate" "$canon_date"; drift=1; continue
  fi
  if [ -z "$sha" ]; then
    printf '[NO ANCHOR]  (%s) %s — content never verified under this scheme\n' "$tier" "$file"; drift=1; continue
  fi
  if [ "$git_ok" = 0 ]; then
    printf '[DATE-OK, UNVERIFIED] (%s) %s\n' "$tier" "$file"; drift=1; continue
  fi
  if ! git cat-file -e "$sha^{commit}" 2>/dev/null; then
    printf '[BAD ANCHOR] (%s) %s — %s is not a commit in this repo\n' "$tier" "$file" "$sha"; drift=1; continue
  fi
  # An untracked file diffs clean against every commit, so without this it would
  # read [OK] forever while nothing about its content was ever compared.
  if ! git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
    printf '[UNTRACKED]  (%s) %s — not in git, so its content cannot be checked\n' "$tier" "$file"; drift=1; continue
  fi
  # Diff the anchored commit against the working tree, ignoring the marker line
  # itself so that stamping the marker cannot invalidate its own anchor.
  body=$(git diff "$sha" -- "$file" | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' | grep -v 'rules-sync:')
  if [ -n "$body" ]; then
    printf '[EDITED SINCE VERIFY] (%s) %s — changed since %s\n' "$tier" "$file" "$sha"; drift=1
  else
    printf '[OK]         (%s) %s @ %s:%s\n' "$tier" "$file" "$mdate" "$sha"
  fi
done < mirrors.list   # lines of  path:tier

[ "$seen" -gt 0 ] || { echo "!! CHECKER BROKEN: zero mirrors parsed"; exit 2; }
if [ "$drift" = 0 ]; then echo "All mirrors in sync."; exit 0; else echo "Drift detected — proceed to Step 2."; exit 1; fi
```

Exit `0` = in sync, `1` = drift, `2` = **the checker itself is broken** (canonical missing, undated, or no mirrors parsed). Exit 2 is not a clean result and must never be read as one.

**Keep exactly one copy of this detector.** If you factor it into a script, delete the inline version rather than leaving both. A drift detector that exists in two places is a thing that can drift from itself, which is the precise failure this command was built to catch.

**Prove the check can still fail.** A green run is worthless if the detector is dead. Back-date one anchor to an older commit for that file, re-run, confirm it reports `[EDITED SINCE VERIFY]`, then restore. Do this before you trust a clean reading — especially the first time you run it on a new mirror set.

## Step 2 — Re-sync anything flagged

Flags do not all mean the same thing:

| Flag | Meaning | What to do |
|---|---|---|
| `[STALE]` | Canonical moved; this mirror was never re-synced. | Full re-sync — the numbered steps below. |
| `[EDITED SINCE VERIFY]` | The file changed since its last verified content. Says nothing about *whether* rule text diverged. | `git diff <sha> -- <file>`, confirm no rule substance moved, then re-anchor to current HEAD. Most will be benign. |
| `[NO ANCHOR]` | Marker carries no SHA — content has never been verified under this scheme. | Read against canonical, then stamp. |
| `[BAD MARKER]` / `[BAD ANCHOR]` | Malformed or future-dated marker; SHA not in this repo. Both silently disable detection for that file. | Fix the marker. Treat the file as unverified until you do. |
| `[UNTRACKED]` | The mirror is not in git, so it diffs clean against every commit. | Commit it, or drop it from `mirrors.list` and pointer-ize the restatement. |
| `[DATE-OK, UNVERIFIED]` | Git layer is down. Content was not checked at all. | Fix git. Do not treat as clean. |

For each `[STALE]` / `[NO MARKER]` file:

1. **Read** the current canonical text and the flagged file.
2. **Tier A** — update the rule block in place, rule by rule, so substance, status, and numbering match canonical. Preserve each file's surrounding framing and its deliberate additions.
3. **Tier B** — read the canonical diff, judge whether it touches this file's subset, update only what's relevant. Never leave a detailed restatement half-updated without an in-file note saying which parts were verified.
4. **Show the operator the proposed change before writing** if it touches rule wording — rules are the one text class where a silent "improvement" is a bug.

## Step 3 — Bump the marker

Order matters: **the content must be committed before you can anchor it.** Commit, take HEAD, then write the marker.

```bash
canon_date=$(grep -m1 '^date_modified:' rules/canonical-rules.md | sed 's/.*: *//' | tr -d ' ')
git status --short -- <file>     # must be clean first
git rev-parse --short HEAD       # this is the anchor
# then edit the marker to:  rules-sync: canonical-rules.md@<canon_date> verified@<today>:<HEAD>
```

Edit the marker with your editor rather than `sed`, so the change is reviewable. Re-run Step 1 to confirm `[OK]`.

**If your agent is not permitted to commit** — a common setup, and a good one for knowledge bases — the file stays `[EDITED SINCE VERIFY]` until whatever does the committing picks it up. Treat that wait as part of the design. The anchor claims a *specific committed state* was read, and until the commit lands there is no such state to claim. Wait for the commit, confirm `git diff HEAD -- <file>` is clean, then anchor. Anchoring at a HEAD that predates your own edit, to make the flag go away, is exactly the unread-stamp failure this field was added to expose.

## Failure modes this version makes loud

Every one of these previously produced a clean-looking `[OK]`, and every one was found by red-teaming the checker rather than by using it:

- **Git layer missing.** The content check used to `2>/dev/null` into an all-green run that was indistinguishable from a healthy one. Now it prints a banner and downgrades every file to `[DATE-OK, UNVERIFIED]`.
- **Future-dated or malformed `verified@`.** A stamp reading `verified@2027-01-01` disabled that file's check permanently and invisibly, because git's date parser never errors on garbage.
- **Unresolvable SHA** — now `[BAD ANCHOR]` instead of a skipped comparison.
- **Marker extraction hijacked by prose.** The grep is anchored to the full two-field pattern. Without that, a sentence *discussing* the marker scheme earlier in a file gets picked up as the marker. Since the entry-point files are exactly the ones that document this scheme, the unanchored version was one paragraph away from poisoning itself.
- **A zero-mirror run reading as success.** An empty or unreadable `mirrors.list` printed nothing and exited clean. Now it exits 2.
- **An untracked mirror reading as verified.** A file that git does not track diffs clean against every commit, so a well-formed marker on an untracked file produced a permanent `[OK]` with nothing ever compared. Caught by running the checker against a fixture set rather than by reading it. Now `[UNTRACKED]`.

## Honest limitations

Stated plainly, because a check whose limits are undocumented gets trusted past them:

- **The anchor is self-asserted.** Nothing forces the stamper to have actually read the file. What the scheme buys is detectability after the fact: the SHA pins exactly what was claimed-read, so a false stamp can be caught later. Call it bookkeeping with receipts and set your expectations there.
- **Canonical has no anchor of its own.** There is nothing to compare it against, so its baseline check stays date-based. That check can still close part of its own gap: it can also diff canonical's working tree against its last commit, so an edit sitting uncommitted is caught immediately rather than waiting for whatever auto-commits the repo. What it still cannot catch is a rule edited *and committed* later the same day without a `date_modified` bump — closing the uncommitted-edit case doesn't close the same-day-committed one. If you hand-edit canonical, bump the date.
- **`[OK]` is not semantic equivalence.** It means the mirror was synced to the current canonical date and nothing has committed against it since.
- **Scope is the tracked set only.** Uncommitted edits are caught, but only for files in `mirrors.list`. Untracked restatements elsewhere stay out of scope by design — pointer-ize those rather than tracking more copies.

Cheap-and-honest beats thorough-and-never-run.
