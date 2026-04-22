# Debrief Skill

## Purpose
Run a full manufacturing floor debrief against available data.

## When to use
- Morning standup preparation
- Post-shift analysis
- On-demand floor intelligence

## Entry point
python agents/debrief/src/main.py

## Tools available
- get_build_metrics()      → structured signals + build data
- get_bottleneck_report()  → blocked work orders only
- get_at_risk_report()     → at-risk work orders only
- flag_for_team()          → route finding to team

## Process
1. Call get_build_metrics() first — signals are pre-computed
2. Reason over signals.blocked before signals.at_risk
3. Call flag_for_team() for each critical finding
4. Generate output in standard format

## Output format
SUMMARY
PRIORITY FINDINGS (blocked / at_risk / needs_decision / pattern)
RECOMMENDED ACTIONS

## Specific to
- Corvus Debrief agent only
