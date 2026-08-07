---
description: Monthly automation health check + skills/commands gap review. Verifies every scheduled job actually fired (artifacts, not logs), then mines the month's session log for workflows that deserve to become skills.
---

# /monthly-audit — automation health + skills gap review

Two jobs, one monthly ritual (run on the **2nd of each month**, so 1st-of-month jobs have had their window):
**Part A** — verify every scheduled automation actually fired, against a single health board file that lists ALL jobs.
**Part B** — review the sessions since the last audit and recommend new skills/slash commands worth building.

## Part A — automation health

Maintain ONE health-board file listing every scheduled job (launchd/cron agents, web monitors, cloud routines, mail scripts) with a per-row **"Proof it fired"** column — the exact command or artifact check that proves the job ran. The board is the checklist. Do not trust the previous audit's status — **verify live; cached state lies.**

### Step 1 — locally verifiable rows

Run the per-row proof commands in parallel, e.g.:

```bash
launchctl list | grep <your-prefix>          # all loaded? exit status 0?
tail -5 <autocommit-log>                     # committed within the last hour?
tail -40 <weekly-job-log>                    # a start/exit block each week since last audit?
```

Then verify **artifacts, not just logs** — the false-green rule:
- A job's log saying "ran OK" is necessary but not sufficient. Check that the artifact it exists to produce (the report file, the inbox item, the changelog line) actually exists for this period.
- A log with output and no artifact is a **silent failure wearing a green checkmark** — the exact failure class this audit exists to catch.

If a job didn't fire, check the board's **Known failure modes** column before diagnosing (machine asleep at the window, plist installed after the window, scheduler PATH differences). A missed window with the machine off is *expected behavior* — note it, don't "fix" it. To prove a trigger after any config change: kickstart the job manually via the scheduler (`launchctl kickstart gui/$(id -u)/<label>`) and re-read the log — a manual script run proves the logic, **only a scheduler-initiated run proves the trigger.**

### Step 2 — remotely verifiable rows

Check hosted monitors/routines via their CLIs or APIs; flag any monitor returning empty results for 3+ consecutive periods (an empty-but-"successful" monitor is another false green).

### Step 3 — CLI-blind rows — stage, don't skip

Some jobs can't be verified from the terminal (cloud routines behind a login, mail-side scripts). Don't silently skip them: **stage each one to a single human action** — open the exact status page in a tab, or ask the one yes/no question. An unverifiable row that's never surfaced becomes a job that's been dead for six months.

### Step 4 — update the board

Update each row's "Last audit status" and the board's **Last full audit** date; add a dated changelog line. Genuinely broken job: fix now if the fix is local and reversible; otherwise flag with a recommendation.

## Part B — skills/commands gap review

1. List the session-log entries since the last audit (filenames carry the topics).
2. Look for **workflows that repeated 3+ times without a skill/command** (the standing rule). Test each candidate: Still recurring next month? Does it have judgment content worth encoding (gates, failure modes, voice), or is it just a prompt? Would a skill have prevented a documented mistake?
3. Cross-check the existing skills/commands surface first — never recommend a duplicate.
4. Flag the inverse too: skills/commands gone **dead** (unused, or their premise retired) as retirement candidates.
5. Check staleness of periodic manual sweeps that are NOT automated (housekeeping, mirror-sync, open-thread census — anything on a "run occasionally" honor system).

## Output

One report in chat, outcome first:
1. **Health board delta** — rows that changed status; one line each on fixes applied.
2. **Skill/command recommendations** — with the evidence (which sessions repeated the pattern), recommendation first.
3. **Retirement candidates + stale sweeps.**

The board update IS the record — don't file a duplicate report.

## Two more audit-design ideas

Learned from surfaces specific enough that the checks that found them don't belong in a template like this — but the underlying ideas travel:

- **A remediation checklist can only cover ground someone already thought to list.** Pair it with an occasional sweep that excludes nothing and assumes every directory could be dirty; its job is finding new surfaces to add to the checklist, not fixing them. A checklist audited only against itself stays blind to whatever it never thought to include.
- **A policy with no technical enforcement is not unauditable — audit its artifact trail instead of the policy.** If a rule says "only X may trigger Y" and nothing in the system actually blocks anyone else from triggering Y, check for Y's own byproducts (files it always writes, timestamps it always leaves) rather than trying to verify compliance directly.

## The transferable pattern

The load-bearing ideas: **one board for all jobs** (scattered automations rot invisibly), **proof-it-fired columns** (every job declares its own verification), **artifacts over logs** (false-green rule), **manual-run ≠ trigger-proof**, and **stage the unverifiable to one human action** instead of skipping it.
