# Student Benefits Closeout — 2026-09-09

**Status:** OPERATIONAL HANDOFF  
**Authority:** `STUDENT_BENEFITS_ENROLLMENT_LEDGER_2026-09-09.md`  
**Email drafts:** `STUDENT_BENEFITS_EMAILS_2026-09-09.md`

> Keep personal identifiers, student numbers, private email addresses, login details, and verification documents out of the public repository. Use the owner's local/password-manager/account context for identity fields.

## Purpose

This is the short execution sheet for claiming verified student / education benefits without re-researching the entire ledger.

## Hard stop

Hand control back to the owner for:

- login, password, MFA, account recovery;
- SheerID / Proxi.ID / school-email verification;
- student ID, transcript, enrollment letters, or government ID;
- payment cards;
- legal terms / privacy consent;
- any application requiring an institutional representative;
- any field asking for company, revenue, funding, or employment claims that are not already true.

Do not store those values in Git.

## Claim order

Work the current ledger queue in order, prioritizing:

1. Kiro Student
2. OpenAI Codex Student
3. GitHub Student Developer Pack / Copilot Student
4. Camber Student
5. Azure for Students
6. JetBrains Student
7. Zed Student
8. Adobe Substance 3D Education
9. Autodesk Education
10. Figma Education
11. Unity Student
12. AWS Student Rewards

For every program:

- use the official URL already recorded in the ledger;
- verify eligibility honestly;
- stop at identity / payment / legal gates;
- after a successful claim, record only non-sensitive status fields that are appropriate for a public repo;
- store private account details outside Git.

## Routing after claims

Use benefits according to workload rather than creating another toolchain:

- routine agent work → low-cost / included student agents;
- hard UE / C++ work → strongest available coding model;
- long CPU/GPU experiments → student cloud / compute credits;
- DCC / mocap benefits → only when they support an active capstone deliverable.

Do not create a second grant tracker or another project authority document.

## Outreach

The existing email-draft file contains the current vendor / faculty outreach wording. Before sending:

- verify the recipient is current;
- remove any unnecessary personal identifiers;
- do not impersonate faculty or an institution;
- do not claim startup status, revenue, funding, or degree type inaccurately;
- log the result in the enrollment ledger at a non-sensitive level.

## Git rule

This file intentionally omits personal identifiers even if they are available locally.

Public repository documentation should contain:

- program name;
- official source URL;
- eligibility notes;
- status;
- renewal / expiry date when non-sensitive;
- next action.

It should not contain:

- student numbers;
- passwords or tokens;
- private verification artifacts;
- government ID;
- account recovery data;
- unnecessary personal email addresses.

## Finish condition

The lane is complete when the priority benefits are either:

- granted;
- blocked on owner identity / legal action;
- honestly ineligible;
- or intentionally deferred.

Then stop. Return to Melodia production.
