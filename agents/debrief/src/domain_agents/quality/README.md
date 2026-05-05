# Quality Agent

Owns lightweight quality signals found in production rows.

Responsibilities:
- Detect QA holds, defects, inspection failures, NCR/MRB/rework/scrap signals.
- Route quality-related findings to Quality Assurance.
- Preserve evidence from source fields and extended CSV columns.

Inputs:
- Evaluated work-order records.
- Notes and extended fields from CSV/MES intake.

Outputs:
- Quality findings.
- Quality summary counts.

