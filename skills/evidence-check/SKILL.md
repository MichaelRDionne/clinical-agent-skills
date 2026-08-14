---
name: evidence-check
description: >-
  Verify a clinical, drug, or evidence claim against primary sources — FDA
  labels (openFDA / DailyMed) and PubMed — when a local reference library
  cannot confirm it, or to cross-check a medical-GPT answer before it ships.
  Free, no API key, no PHI in queries.
---

# evidence-check — verify against primary sources

The second tier of a "gold sources before web" protocol. Order of checks:

1. **Local reference library first** — the textbooks and manuals already on disk
   (psychopharmacology handbooks, DSM, board-prep manuals, specialty diagnostic
   texts). Cite those when they cleanly cover the fact.
2. **This skill** — when the library cannot confirm it: a **label / currency**
   question (is X approved for Y? boxed-warning status?), a specialty fact
   outside the local books, or **recent literature**. Hit FDA + PubMed directly.
3. **General web search** — only if neither covers it.

These are **free public APIs**. No key, no MCP required.

## Firewall

- **No PHI in any query.** Send only drug names, clinical concepts, or generic
  questions — never a patient identifier, name, MRN, or case detail tied to a
  real person. Fictional teaching cases are fine; real patients never.
- Use the operator's actual licensed title in any prose this check feeds.
- The public endpoints carry no PHI risk. The constraint is what you *send*.

## The endpoints (verified fetchable)

**FDA drug label — openFDA** (cleanest for "what does the label say"):

```
https://api.fda.gov/drug/label.json?search=openfda.brand_name:<BRAND>&limit=1
https://api.fda.gov/drug/label.json?search=openfda.generic_name:<GENERIC>&limit=1
```

Fetch it with a prompt like: *"From this FDA label JSON, quote the
indications_and_usage / boxed_warning / warnings section verbatim for <drug>;
is it approved as monotherapy or adjunct for <indication>?"* Returns the
authoritative current label.

**DailyMed** (alternate label source, SPLs):

```
https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name=<NAME>
```

**PubMed literature — NCBI E-utilities** (two steps):

```
# 1) search → get PMIDs + count
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<QUERY+terms>&retmax=5&retmode=json
# 2) summaries for those PMIDs (titles/journal/year)
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=<PMID,PMID>&retmode=json
# (abstracts if needed)
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<PMID>&rettype=abstract&retmode=text
```

URL-encode spaces as `+`. Prefer reviews and guidelines; note the year
(currency matters).

**FAERS adverse-event signal (optional):**

```
https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:<NAME>&count=patient.reaction.reactionmeddrapt.exact
```

## Procedure

1. State the **claim** to verify (one line).
2. Pick the source: drug-label fact → openFDA; literature / evidence → PubMed;
   both if useful.
3. Fetch, extracting the specific section (quote the label; list PMID titles
   and years).
4. Return a verdict: **CONFIRMED / REFUTED / NUANCED**, with the
   **primary-source quote + URL + date**.
5. If the check feeds teaching-case content, give the board-style answer first
   and put label / currency nuance in parentheses.

## Absence traps — never conclude "no such FDA document exists" from a bare fetch

- **`accessdata.fda.gov` returns a ~420-byte stub with HTTP 200 to a default
  `curl` User-Agent.** The 200 makes it look like a successful fetch of an empty
  result, and it has already produced a false "no FDA letter exists." **Set a
  real browser User-Agent before concluding an FDA document is absent**, and
  sanity-check the response size — a few hundred bytes is a stub, not a
  document. Same failure class as WAF bot-blocking on ordinary sites.
- **Verify negative findings generally.** "I searched and it isn't there" is a
  claim that needs the same evidence as a positive one. State the query you ran
  and the surface you searched, or don't assert absence.

## When not to use

- A fact the local library already cleanly covers → cite the library, skip
  the web.
- Anything requiring a real patient's data → stop (PHI).
- Legal / jurisdictional questions (state duty-to-warn statutes, for example)
  → that is legal research, not FDA / PubMed.

## Proven examples

- **Esketamine monotherapy** (a 2024 handbook too old to confirm) → openFDA
  label: *"…indicated for Treatment-resistant depression (TRD) in adults, as
  monotherapy or in conjunction with an oral antidepressant."* CONFIRMED.
- **Levetiracetam behavioral effects** → PubMed esearch returned a large,
  reviewable set for a teaching-case claim.
