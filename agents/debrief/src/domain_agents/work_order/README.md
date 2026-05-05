# Work Order Agent

Owns production work-order status and readiness signals.

Responsibilities:
- Normalize raw rows into canonical work-order records.
- Identify blocked, delayed, stalled, at-risk, unassigned, and decision-needed work.
- Produce production-owned findings with evidence.

Inputs:
- Raw MES-like build/work-order rows.
- Customer thresholds from onboarding.

Outputs:
- Enriched build records.
- Summary counts.
- Signal groups.
- Work-order findings for the debrief workflow.

