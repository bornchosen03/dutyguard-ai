# DutyGuard First-Customer Playbook

## Objective
Land the first importer customer with a low-risk pilot and clear recovery economics.

## Offer Structure
- Free tariff leakage assessment for 50–100 historical entries.
- Paid pilot only on validated opportunities.
- Commercial model: contingency fee + optional minimum floor.

## 2-Week Execution Sprint

### Week 1 (Trust + Safety)
1. Finalize review workflow: `open -> approved/rejected`.
2. Keep immutable audit trail for every review decision and packet generation.
3. Generate a customer-facing `why this classification` report.
4. Enforce policy thresholds for auto-flag/manual-review.
5. Ensure legal disclaimers appear in all decision outputs.

### Week 2 (Customer Ops + Proof)
1. Run pilot onboarding with real customer entries.
2. Prioritize top duty-leak opportunities by potential recovery.
3. Export claim packet for legal/customs review.
4. Produce 2–3 sample recoveries with confidence notes and before/after deltas.

## Practical First-Customer Steps
1. Get one warm intro from a broker/forwarder/trade advisor.
2. Run free audit on historical entries.
3. Present Top 10 recoverable opportunities with confidence + review notes.
4. Convert to paid 30–60 day pilot.
5. Turn pilot output into first case study.

## Talk Track (What to Say)
- "We find recoverable duty leakage in your historical entries and rank opportunities by impact and confidence."
- "Every high-risk recommendation is routed to human review with a full audit trail."
- "You receive a claim-ready packet with rationale, legal citations, and confidence intervals."
- "We align fees to outcomes via a contingency model."

## Demo Flow (What to Show)
1. Upload/import entries (`/api/pilot/onboard`).
2. Opportunity ranking (`/api/pilot/prioritize/{batch_id}`).
3. Review queue (`/api/reviews`, `/api/reviews/{id}`, decision endpoint).
4. Classification report (`/api/classification-report/{review_id}`).
5. Claim packet output (`/api/pilot/claim-packet/{batch_id}`).
6. Metrics snapshot (`/api/metrics/summary`).

## Guardrails
- This system provides decision support, not legal advice.
- Final classification and filing determinations require qualified customs/legal professionals.
- Do not present model output as a final legal decision without reviewer sign-off.
