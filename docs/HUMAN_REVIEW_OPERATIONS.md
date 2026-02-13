# Human Review Operations (SOP)

## Purpose
Ensure high-risk or low-confidence tariff/tax decisions receive consistent human review before final customer action.

## When a Case Requires Human Review
A case must be queued for review when any of the following apply:
- Confidence is below internal approval threshold.
- Risk score is high due to ambiguous description/material/origin/value.
- Policy or legal disclaimer conditions are triggered.
- Customer explicitly requests manual confirmation.

## Review Queue Lifecycle
Status flow:
- `open` -> initial state
- `approved` -> reviewer confirms recommendation
- `rejected` -> reviewer rejects recommendation and records rationale

## Reviewer Checklist
For each ticket, reviewer should:
1. Confirm product description and intended use are specific and complete.
2. Validate origin country and material composition evidence.
3. Cross-check rationale against current internal policy/source references.
4. Confirm legal disclaimer and confidence notes are present.
5. Record clear decision rationale suitable for audit.

## Decision Standards
- Approve only when classification rationale is evidence-backed and policy-aligned.
- Reject when key evidence is missing, contradictory, or confidence is materially low.
- If rejected, include what evidence is required for resubmission.

## Audit & Compliance
- Every review decision must be appended to immutable audit logs.
- Keep ticket payload, reviewer decision, and timestamp together.
- Preserve generated claim packets and classification reports for traceability.

## Operational SLAs (Suggested)
- New `open` tickets triaged within 4 business hours.
- High-value/high-risk tickets reviewed within 1 business day.
- Non-urgent tickets reviewed within 2 business days.

## Escalation Path
Escalate to compliance/legal lead when:
- Regulatory interpretation is uncertain.
- Customer-submitted data appears inconsistent or unreliable.
- Potential financial/legal exposure exceeds pilot thresholds.

## Pilot-Ready Controls
Before production customer rollout, confirm:
- Review endpoint permissions are restricted to authorized staff.
- Decision reason is mandatory for `approved` and `rejected` outcomes.
- Metrics include queue volume, turnaround time, and approval/rejection trends.
- Sample audit log entries are verified in staging.
