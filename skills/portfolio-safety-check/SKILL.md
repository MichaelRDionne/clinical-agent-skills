---
name: portfolio-safety-check
description: >-
  Pre-publish safety audit for a professional's public GitHub presence. LOAD BEFORE:
  creating any new public repo, pushing new content to an existing public repo, flipping
  ANY repo from private to public, editing the profile README, publishing a gist or
  Pages site, or running a periodic full-portfolio audit. Catches what generic
  PHI/secrets scanners miss: real employer/practice names, real vendor/product names
  tied to a real job, real colleague names, described production architecture,
  agentic-workflow artifacts, git-history leaks of deleted files, and
  inference/combination risk.
---

# portfolio-safety-check — pre-publish audit

Built for a licensed clinician building a public GitHub portfolio as proof-of-aptitude for healthcare-AI roles. The portfolio must demonstrate real engineering skill **without letting a reader connect any repo back to a real workplace, vendor account, colleague, or patient**. Generic secrets/PII scanners don't catch the highest-risk category here: **real-world identifying context**. No credential regex flags your employer's name in a README. This skill does.

**Why the bar is this high:** for a licensed professional, anything public that ties their name + a real employer + descriptions of production tooling is discoverable, quotable, and permanent (forks, caches, the Internet Archive). The standard is not "no PHI" — it's "a motivated reader cannot map this repo onto a specific real workplace or person."

## The cautionary tale

Two live public repos were found naming the real employer and the real EHR vendor while describing actual production clinical-automation tooling, with tool names carrying the vendor's initials as a prefix. No PHI, no secrets — and every generic scanner would have passed them. Both were flipped private, genericized (real vendor → "a cloud-based EHR", vendor-prefixed tool names → generic prefixes), verified live, and republished.

**Follow-up, twelve days later — history was NOT actually purged.** A re-audit found the genericization had only edited the working *tree* forward; a fresh clone + `git log --all -p` of both still-public repos returned 13 hits for the real names in history. Tree was clean, history was not. Remediated by squashing each repo to a single clean commit and force-pushing (`git checkout --orphan` → commit → force-push); verified live from independent fresh clones at **`hits: 0, commits: 1`**. Lesson: **"genericized and verified live" checks the tree, not the history — always re-run `git log --all -p | grep`, not just a raw-README curl.** A force-push flattens the branch but GitHub keeps unreferenced commits by SHA until GC; for a *credential* (vs. an employer name) escalate to delete-and-recreate + a GitHub Support cache purge.

## The standing rule

**This check runs BEFORE any repo visibility change to public — every time, not just at creation.** A repo clean at creation can accumulate unsafe content later. The gates:

1. New public repo → audit the working tree before the first push.
2. New content into an existing public repo → audit the diff before push.
3. **Private → public flip → full audit (tree + history) first. No exceptions.**
4. Quarterly (or before any job application that spotlights the GitHub link) → full portfolio sweep.

If the principal says "just flip it, it's fine" — run the check anyway; it takes two minutes. Surface findings; they decide. Never flip visibility yourself without the check having run.

## What to check — priority order

Ordered by *distinctiveness of the risk*: (a)–(c) are what nothing else catches; (d)–(f) are table stakes; (g) is the reasoning layer.

**(a) Real employer / practice names.** Any current or past employer or facility name. The principal's own public brand is their call, not an automatic hit — but flag it so the association is deliberate, never accidental.

**(b) Real vendor / product names tied to a real job.** The EHR vendor, the covered-AI vendor account, any SaaS used *at work* — naming them describes the real production stack. Generic mentions in coursework ("built a demo against a public FHIR sandbox") are fine; "my daily workflow automates <vendor>" is not. The tell: does the text describe **their** operational use, or a generic/tutorial use?

**(c) Real colleague, contact, supervisor, or (obviously) patient names.** Any personal name other than the principal's own. Also usernames, email handles, and chat display names in pasted logs.

**(d) Standard PII/secrets patterns:** API keys and tokens (`sk-`, `ghp_`, `AKIA`, `xox[bap]-`, `AIza`, private-key headers), emails, phone numbers, `.env`/credential files, absolute home-directory paths (they leak the machine username and directory layout).

**(e) Agentic-workflow artifacts.** `handoff*.md`, session logs, `.claude/`, `.codex/`, `CLAUDE.md`, `AGENTS.md`, transcripts, scratchpad dumps. Two risks: they carry working context (paths, names, live project state), and internal files can carry internal-only vocabulary. Note the distinction: a repo *shipping a skill/agent config as its product* is fine; a repo that *accidentally includes its own development session residue* is not.

**(f) Git history.** Deleted files are not gone — they live in every clone's history until history is rewritten. A file scrubbed from the tree but present in an old commit is still fully public. Scan `git log --all`, not just HEAD.

**(g) Inference / combination risk.** No single field sensitive, but the combination identifies: "a small practice in [city]" + a role + a panel description; a distinctive tool architecture only one real deployment matches. Also: any legal/regulatory-matter vocabulary the principal's rules ban from public text must never appear in any public repo in any form. This is the layer regex can't do — read the prose as a hostile identifier would.

## Step 0 — re-fetch before you push (concurrency, not content)

Assume a parallel session has already pushed. If the principal runs multiple agent sessions at once, two sessions can hold clones of the same repo — and a force-push from a stale clone silently destroys the other session's work. This happened in the originating setup: three concurrent sessions hit the same repos in one day, twice clobbering a 15-file expansion via orphan-squash force-pushes from stale clones. It was recovered only because GitHub retains dangling commits for a few weeks (`gh api repos/OWNER/REPO/tarball/<sha>`). Do not rely on that a second time.

Before **any** push, and again immediately before any force-push:

```bash
git fetch origin
git status -sb | head -1              # ahead/behind — behind means someone pushed
git log --oneline HEAD..origin/HEAD   # empty means you are current
```

Non-empty output means re-clone or rebase before continuing. An audit of a stale tree certifies content that is no longer what the repo holds.

## The runnable procedure

Run against a **freshly fetched** local clone (`gh repo clone <user>/<repo> /tmp/audit-<repo>`).

### 1. The personal match list (the layer generic tools lack)

Maintain a **private** file of the specific terms that must never appear publicly — employer names, workplace vendor names, colleague names, matter-specific vocabulary. It lives in your private notes, NEVER in a public repo (this public copy uses placeholders):

```bash
# Working tree — real-world identifying context (SUBSTITUTE YOUR OWN TERMS)
grep -rniE --exclude-dir=.git \
  'employer-name|ehr-vendor-name|vendor-prefix-|colleague-1|colleague-2|attorney-name' .

# Matter vocabulary — zero tolerance in anything public (SUBSTITUTE YOUR OWN)
grep -rniE --exclude-dir=.git \
  'regulator-name|case-number|matter-specific-phrase' .
```

Interpretation: **any hit on an employer/vendor/person term in a public-bound repo is a finding** — the question is only whether it's (i) genericize, (ii) delete, or (iii) a deliberate, principal-approved self-reference. Short prefixes will false-positive — eyeball each hit; don't bulk-dismiss.

### 2. Standard secrets/PII sweep

```bash
grep -rniE --exclude-dir=.git \
  'sk-[A-Za-z0-9]{20}|ghp_[A-Za-z0-9]{20}|gho_|AKIA[0-9A-Z]{16}|xox[bap]-|AIza[A-Za-z0-9_-]{30}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY' .
grep -rniE --exclude-dir=.git \
  '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|\(?[0-9]{3}\)?[-. ][0-9]{3}[-. ][0-9]{4}' . \
  | grep -viE 'example\.com|noreply|users\.noreply\.github|schema|@types'
grep -rn --exclude-dir=.git '/Users/<your-username>' .
```

If `gitleaks` is installed, `gitleaks detect --source . -v` replaces the first block and adds history coverage. Don't block on installing it — the greps cover the categories.

### 3. Agentic artifacts

```bash
find . -path ./.git -prune -o -type f \( \
  -name 'handoff*.md' -o -name 'CLAUDE.md' -o -name 'AGENTS.md' \
  -o -name 'session*.md' -o -name 'chat-*.md' -o -name '*.transcript*' \) -print
find . -maxdepth 3 -type d \( -name '.claude' -o -name '.codex' \) -not -path './.git/*'
```

Each hit: is it the repo's deliberate product, or session residue? Residue → delete AND check history (step 4).

### 4. Git history — deleted files and past content

```bash
# Every path that ever existed, incl. deleted — eyeball for artifact/credential names
git log --all --pretty=format: --name-only --diff-filter=A | sort -u

# Match-list terms anywhere in any historical blob
git grep -iE '<your-match-terms>' $(git rev-list --all) -- . | head -50
```

A hit only in history of a repo going public → either rewrite history (`git filter-repo`), or — usually simpler — **create a fresh repo from a clean export of the current tree** (or orphan-squash + force-push) and verify from an independent fresh clone. History rewrite on an already-public repo does NOT purge existing forks/clones/caches; treat anything that was public as permanently exposed and assess accordingly.

### 5. Inference pass (manual, non-optional)

Read the README and any prose docs start to finish, asking: *if I knew the principal's name and profession, could this text point me to a specific employer, vendor account, colleague, or matter?* Combinations count. This pass cannot be scripted — do it every time.

### 5b. Claim-honesty pass (manual, non-optional — same read-through as step 5)

Step 5 asks whether a hostile reader can map the repo onto a real workplace. This pass asks the different question: **can the principal defend every claim in this repo in an interview?** Portfolio repos exist to be read by recruiters and hiring managers; an inflated claim is a different failure than a leak, and it fails in the room instead of on the internet. No grep finds it. Run it on the same pass as step 5 — it costs almost nothing extra.

What to flag:

- **Habitual present tense for work never done.** "The consulting flow I use," "my clients," "engagements I run" — present-tense-habitual implies an ongoing practice. Compare against reality: has the principal actually done this *for someone else, for money*? The honest register is either past tense about real work, or conditional ("how I *would* evaluate a vendor"). The conditional costs nothing and survives scrutiny.
- **Cross-references that 404.** Any repo, URL, or demo named in a public README — verify it actually resolves publicly:
  ```bash
  for r in <names>; do printf '%-45s ' "$r"; curl -s -o /dev/null -w '%{http_code}\n' \
    "https://github.com/<user>/$r"; done
  ```
  A private repo listed as a "public build" reads as padding whether or not it was.
- **Unqualified "production."** True for the principal's own daily-use tooling; an engineering reader hears multi-user, on-call, SLA. Qualify it — "in daily production use in my own practice" is airtight where bare "production-grade" is arguable.
- **Plurals covering a single instance.** "UIs," "systems," "clients," "deployments."
- **Manufactured audience.** Named communities the principal didn't post to, implied inbound interest, "as featured in."
- **Real work disguised as synthetic.** The inverse failure, and easy to miss: anonymizing genuine shipped builds into vague "case studies" makes them read as invented. Label real work as real. If naming the venture is the safety problem, "live build, site unnamed" gets the credibility without the linkage — and note the deliberate anonymity in the repo's own agent-instructions file so a later session doesn't "fix" it by naming things.
- **Internal contradictions.** A blanket "everything here is synthetic" sitting above sanitized production docs; a "next build ideas" list naming something already shipped. These signal the README wasn't re-read after edits, which is itself what a careful reader notices.

Disposition is the principal's, same as step 5 — surface each one with the specific line; don't silently rewrite their voice. And fixing an honesty problem by *naming* a previously-anonymous venture is a step-5 decision, not a step-5b cleanup: that trade is the principal's call every time, even when the honesty fix is obviously correct.

### 6. Portfolio-wide sweep (periodic mode)

```bash
gh repo list <user> --limit 100 --json name,visibility,description,updatedAt
# Cheap first pass across public code without cloning:
gh api 'search/code?q=user:<user>+<term>' --jq '.items[].repository.name'
```

`search/code` only indexes default branches of larger/active repos and lags pushes — a clean search result is a *screen*, not a clearance. Any repo flagged, or about to be spotlighted, gets the full clone-and-audit (steps 1–5).

### What "clean" looks like

- Steps 1–4 produce zero unexplained hits (each remaining hit has an explicit "deliberate, approved" disposition).
- Step 5 read-through: an outside reader gets "clinician-developer who builds clinical automation against a cloud-based EHR" and nothing more specific.
- Step 5b read-through: every claim is one the principal can defend in an interview — real work named as real, unbuilt work in the conditional, every cross-reference resolving publicly.
- **State the QC actually run:** list the commands executed and hit counts, not "looks fine."

## Remediation — the pattern that already worked

Order matters. Private-first because it's fast, reversible, and stops new indexing while you work.

1. **Flip private immediately:** `gh repo edit <user>/<repo> --visibility private --accept-visibility-change-consequences`. Do this before perfecting the fix.
2. **Genericize, don't gut.** Keep all the engineering substance — architecture, code, metrics, lessons. Replace only the identifying nouns: real employer → "a clinical practice"; real EHR vendor → "a cloud-based EHR"; vendor-prefixed tool names → generic prefixes (renamed consistently across code, docs, and repo description); colleague names → roles. The demo value survives fully genericized.
3. **Check history** (step 4). Historical-only exposure in a repo that was public → fresh-repo or orphan-squash route.
4. **Push, then verify LIVE — never trust the push as proof:** fetch the raw served content post-flip; old terms absent (`curl ... | grep -icE '<terms>'` must be 0), renamed paths 404, new generic text is what's actually served. And clone fresh + `git log --all -p | grep` — tree-clean is not history-clean.
5. **Log it** — a dated line in your session log: repo, what was found, disposition.

## When NOT to use this

- Internal knowledge-base content, outbound email, website copy → your general content rules, not this skill. This governs GitHub only.
- **If actual patient data ever appears in a repo**, that's not a genericize-and-republish event — flip private, do NOT republish, and stop for the principal.
- Private repos staying private → no audit needed to keep working; the gate fires at the visibility boundary. (But content written as-if-public costs nothing.)

## Maintenance triggers

(1) New employer, vendor, or named work contact → add to the private match list the same session you learn of it. (2) A new public surface class (Pages site, gists, org account) → extend the sweep commands. (3) Any future incident → append what was missed and which check would have caught it.
