# Submission checklist

The topic proposal is already approved. This checklist tracks remaining
evidence and student-owned tasks against the supplied 50/40/10 rubric.

## Final report — 50%

| Requirement | Status / evidence |
|---|---|
| System, assets, attacker capabilities, and assumptions | Drafted in `final_report.docx` and `.pdf` |
| Primary RBAC mechanism and supporting server-side checks | Drafted, with role/permission table and implementation locations |
| Mechanism-to-threat rationale and security properties | Drafted: task confidentiality, integrity, least privilege |
| Concrete failure case | Baseline cross-owner read/update/delete contrasted with hardened denial |
| Reproducible implementation and README | Instructions and tests are in the project; review from a fresh clone after publishing |
| AI Appendix | Included; each student must accurately complete the student-verification disclosure |
| Final student review | Pending: check technical claims, citations, course terminology, formatting, and team requirements |

## Demo and presentation — 40%

| Requirement | Status / evidence |
|---|---|
| 10-minute explanation and demonstration | Nine-slide deck has speaker notes and a 10-minute timing plan |
| Success case | Automated same-owner and admin tests pass; rehearse live |
| Failure case | Automated baseline cross-owner test passes; rehearse baseline then identical hardened request |
| Q&A defense | Likely questions are noted in speaker notes; each member should rehearse |
| TA-selected request and same-owner control | Pending live defense rehearsal with the TA's selected accounts/request |
| Live demo data | Pending: confirm all four members and privately enter their last-two-digit suffixes |

## Participation — 10%

| Requirement | Status / evidence |
|---|---|
| Individual reflection and contribution assessment | Template provided; every student must complete and submit their own |
| Presentation participation | Each student must report their actual role in their individual reflection |
| Group member evaluations | Each student completes the evaluation section based on observed contributions |

## Publication and final run

- Publish both `hardened` and `baseline` branches to the public repository;
  neither branch has been pushed from this workspace yet.
- Confirm the fourth member's name and complete the reflection template's roster.
- Seed the live demo from the four private suffixes; do not commit suffixes or
  local demo database files.
- From a fresh checkout, install requirements, run the tests, start both modes,
  and rehearse the exact cross-owner attack, denied replay, and same-owner
  success. Do not expose the baseline beyond loopback.
