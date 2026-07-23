---
description: Token-saving clinical-note rewrite mode - patch changed sections only, preserve unchanged clinical text exactly, and only print the full note at the end.
---

# /token-saver — patch-don't-rewrite note editing

Use this when a clinical note or chart draft is already in the chat and the clinician needs focused edits without burning tokens on repeated full-document rewrites.

Expected input:

```text
/token-saver
```

Optional input:

```text
/token-saver Update the assessment for anxiety and make the plan match it.
```

## Operating mode

For this session, follow these rules unless the operator explicitly says otherwise:

1. Do not rewrite or reprint the full document by default.
2. Return only changed sections.
3. Preserve unchanged wording exactly.
4. Preserve the existing Markdown structure, heading levels, bold text, bullets, and numbering unless the task is specifically formatting cleanup.
5. If an assessment changes, update only the plan items, risk statements, monitoring items, and follow-up language that directly depend on that assessment.
6. Do not invent new clinical content while doing formatting-only cleanup.
7. At the end of each response, list the sections changed.
8. Ask before printing the full final note.

## Model/effort settings

Match the model tier and reasoning effort to the edit class — this is where most of the savings live:

* Markdown or bold-heading cleanup only: smallest model, lowest reasoning.
* Patch-style section rewrite: mid model, low reasoning.
* Assessment-to-plan propagation: mid model, medium reasoning.
* Clinical reasoning before changing a diagnosis, medication, or safety plan: strongest model, high reasoning.
* Reserve the top effort tier for genuinely stuck tasks or broad whole-chart reconciliation.

The asymmetry is deliberate: formatting mistakes are cheap and visible; a silently propagated clinical error is neither. Spend reasoning where the failure mode is dangerous, not where the diff is large.

## Default response format

When applying edits, respond in this shape:

```markdown
## Changed Sections

### <Section Name>
<replacement text for that section only>

## Change Log
- Updated <section> to reflect <brief reason>.
- No full-note rewrite performed.
```

## Full-note rule

Only print the full note when the operator says something like:

```text
Now print the full final note.
```

When printing the final full note, keep the latest patched sections and preserve all other sections from the most recent accepted draft.

## Why this exists

Iterating on a long clinical note by full rewrite has two failure modes: token cost scales with document length instead of edit size, and every full rewrite is a fresh chance for the model to silently "improve" clinical wording that was already correct. Patch-mode fixes both — the unchanged text is never regenerated, so it can never drift.
