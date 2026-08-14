---
name: outbound-send-gate
description: >-
  LOAD BEFORE staging ANY outbound message in any lane — opening a compose
  window, editing or pasting a draft, clicking compose controls, filling an
  external form, recording anything as "sent", or resuming a half-staged batch.
  Core law: the operator sends; agents stage. Process gates only — the content
  firewall is a sibling skill.
---

# outbound-send-gate — the operator sends; agents stage

The rule existed as an intention and was violated anyway. One email reached a
real recipient with no operator review — a click meant for "minimize" landed on
**Send** because the compose popup's layout had shifted since the screenshot the
coordinates came from. The content happened to be clean. The process was not.
"Be careful" does not survive contact; the gates below are what does.

Every gate names the incident that created it. If a gate is inconvenient, the
gate is working — do not reason around it.

## Scope

Any message that leaves the operator's machines addressed to a real person or
organization, in any lane and under any brand: professional mail, outreach,
applications, portal messages, DMs, contact forms. **A web form's Submit button
is a Send button.** Internal knowledge-base writes are not.

Named exceptions are written, narrow, and explicit. A prior "go" on the batch
never implies a send. A successful send-call is not delivery.

## Per-item state — staged is not sent

Every item in an outreach batch or send log carries exactly one state:

| State | Meaning | Who/what can set it |
|---|---|---|
| `DRAFTED` | Body text exists locally; nothing in the outbound tool yet | agent |
| `STAGED` | A draft exists in the tool, verified per Gates 3–5 (recipient, subject, full body, From) | agent, after verification only |
| `SENT` | The operator reviewed and sent it | **only** a Sent-folder/receipt check |
| `SENT-IN-ERROR` | It went out without the operator's review | receipt check + immediate disclosure |

Transition rules, each paid for:

- **`SENT` is set only from a receipt** — the message found in Sent (or the
  portal's submission confirmation), never from "I clicked send-adjacent things"
  or "the operator said they would send it." A letter recorded as sent was
  actually only staged; the reverse also happened — a letter recorded as an
  unsent draft was already in Sent. The log had to be corrected both directions.
- **`SENT-IN-ERROR` never upgrades to `SENT`.** An accidental send is not
  retroactively "reviewed and approved" in any accounting of the batch, even
  when the content was clean.
- A send log lives next to the batch, recording per item: recipient, timestamp,
  **From identity actually used**, and state.

## The gates

### Gate 1 — Sent-count sentinel around every staging session

Before touching any compose surface, capture the sent count for the identity in
play (Gmail: `in:sent from:<address>`). Re-check after. The two numbers must
match, and the match goes in the close-out. "The draft looks right" and "nothing
went out" are different claims — the misfire was discovered only by accident
because nobody was watching Sent. A later run used the sentinel (4 before, 4
after) and could prove zero sends.

**The sentinel must cover every identity that can send from the surface in play,
not just the one being staged.** A brand-address-only sentinel held steady
through a session in which a real send happened — the letter went out From the
personal address, a second send-as identity on the same account that a
brand-only count cannot see. Capture a sentinel per configured identity; re-check
all of them after. A single-identity sentinel holding steady is proof that
identity sent nothing. It is never proof that nothing went out. Scope the
close-out claim to match.

### Gate 2 — never a cached coordinate near a Send control

No click on or near a Send / minimize / close row may use coordinates from an
earlier screenshot. Gmail's compose popup re-lays itself out every time a
recipient chip confirms or the window reopens from minimized. Get a fresh
element reference immediately before the click — or do not put the cursor in
that neighborhood at all. The URL-prefilled full-window compose
(`?view=cm&fs=1&tf=1&to=…&su=…&body=…`) has a stable layout with Send nowhere
near anything the agent touches, and it eliminated the failure class in the
next batch (11 letters, zero accidental sends).

### Gate 3 — verify the clipboard immediately before a sensitive paste

The system clipboard gets silently overwritten by unrelated background activity.
A paste meant for a letter body once dropped a stray URL instead. Run
`pbpaste | head` in the same breath as the paste — copying earlier in the
session proves nothing. Better: use the URL-prefill path and skip the clipboard.

### Gate 4 — verify the SAVED draft, never the compose window

A draft that looked complete in the compose window was silently truncated to one
line on save. The operator caught it before the agent did. Verification happens
against what the tool actually stored: reopen the draft fresh, or run
draft-search checks. The three-way pattern for batches: `in:draft from:<identity>`
count, a per-item `to:` search for recipient chips, and a body-phrase search
(a phrase every letter contains) whose hit count proves no body truncated on save.

### Gate 5 — confirm the From identity per compose, from the DOM

The account's **default send-as is often the personal address**; brand identity
must be selected on every compose and the selection fails silently when rushed.
Two letters in one batch went out under the personal address this way. Confirm
From from the DOM (`input[name="from"]` values), never from a screenshot — the
header collapses once the body has focus. Record the From actually used in the
send log.

**Staging the From does not protect the send.** Five letters were staged in
Gmail web with the brand From verified in the saved-draft DOM, and all five went
out from the personal address. Cause: the operator opened the drafts in a
desktop mail client and sent from there. The send-as alias is a server-side
identity; the desktop client did not inherit it and silently substituted the
account address.

Two consequences:

- **Name the send surface, not just the draft.** A staged draft is only
  identity-safe if the sending client actually knows the alias. "It's staged and
  verified" reads as "safe to send from anywhere," and it is not.
- **A wrong-identity send poisons the whole thread.** The recipient replies to
  the address that reached them, so later replies default to that address. Set
  From manually on each subsequent reply in a poisoned thread and re-verify.

Two ways the sentinel lies, both found in production:

1. **Unchanged ≠ zero sends.** `in:sent from:<brand-address>` holding steady
   across a window in which sends demonstrably happened means "zero sends under
   that identity," not "zero sends."
2. **The count is THREADS, not messages.** Gmail search results are
   conversation-collapsed. Three replies sent into three threads that each
   already contained a brand-identity message moved the count by **one**, not
   three. A batch of N replies into existing threads can move the sentinel by
   anywhere from 0 to N while every send is correct.

**Never put a `Delete forever` control in a fallback selector chain.** A
compound selector like `div[data-tooltip="Delete forever"], div[aria-label="Delete"], …`
is harmless in a Drafts view where no permanent-delete control exists — and in
Trash or Spam the same chain matches the **unrecoverable** delete first. Name
the one control you mean, in the one view you are in, and verify the view
before clicking.

**Deleting from a conversation-collapsed list is a CONVERSATION-level delete.**
Three draft rows deleted from a Drafts list trashed **12 real messages** across
those threads — incoming mail with attachments and already-sent replies — while
the Drafts count fell by only 3, which hides it. Recipients are unaffected;
nothing is un-sent. Restore one message at a time. Say so, because the restore
puts everything in INBOX, including messages that only ever lived in Sent.

Consequence: the count is a **screening** check, never proof. Proof is
per-message — open each thread and read the sender on the message you just
sent. Do that for every item in a batch.

### Gate 6 — a permission stop is a stop

When the automation-permission layer blocks a bulk action, surface it to the
operator and wait. Do not route around it (`location.href`, alternate surfaces).
A run that hit this, stopped, and resumed on approval is the correct trace.

### Gate 7 — source or `[TO FILL]` for first-person practice claims

Inside every paste-ready block, inspect first-person factual claims about the
operator's practice, habits, history, or credentials. Each one needs a
traceable source, or `[TO FILL]` for the operator to supply. Anything else is a
red gate.

Detection handle: `I send`, `I've landed on`, `my approach is`, `in my practice`,
`I always`, `what I do is`. The grep only flags candidates — a human decides
whether a claimed habit is real, because nothing mechanical can tell an invented
one from a true one.

A paste-ready block once drafted "After any med change I send the therapist two
lines…" in the operator's voice, unflagged. Had it been pasted, the operator
would have published a fabricated claim about their own clinical practice under
their own name.

## Which identity, which lane

Do not guess an address. Keep a verified table and stop when a lane has no
verified send identity on record.

| Lane | Rule |
|---|---|
| Brand / practice mail | The brand send-as. It is usually **not** the account default — select it every compose (Gate 5). |
| Job applications | The address printed on the resume. Applications must match it. |
| Personal | The personal account address. |
| Employer / staff mail | The dedicated work login, verified live — sessions are not durable. Confirm identity from the account-switcher, never from an empty From field. |
| Any lane with no verified identity | Stop and confirm with the operator before staging. |

## Forms and portals

- The final Submit is the operator's click, always. Stage the form fully filled
  and stop there. Forms with visible reCAPTCHA already end at the operator's
  click by necessity — the gate applies equally when no CAPTCHA forces it.
- Grant / application assistants never submit and never fill a portal.
- Job-application flows pause at a Gate-1-style checkpoint — the operator
  confirms before the final submit fires, and the tracker row records
  submitted-vs-staged per the state table above.

## After an erroneous send

1. **Disclose to the operator immediately, before doing anything else** —
   including before continuing the batch. Not at close-out, not after a fix
   attempt.
2. Check the undo-send window; use it if still open.
3. Mark the item `SENT-IN-ERROR` in the send log with timestamp and From
   identity. It is never counted as reviewed.
4. Remediation is **the operator's call, and "do nothing" is a live option** —
   a duplicate often reads worse than a personal From. Do not auto-correct
   outbound with more outbound.
5. Record root cause and, if a new mechanism surfaced, extend this skill.

## Relationship to the rest of the surface

- A sibling change-control skill owns the confirm-before-outbound one-liner;
  this file is that line expanded into mechanics for the send lane.
- Content-firewall / brand-voice skills govern **what the message may say**.
  This skill assumes content already passed those and governs only how it moves.
- The house pattern is the same as `clinical-change-control`: every rule ships
  with the incident that created it.
