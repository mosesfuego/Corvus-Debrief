# Corvus Debrief User Journey

This document describes the expected path from first checkout to a useful
manufacturing debrief.

## 1. Try the Zero-Setup Demo

The fastest validation path is:

```bash
python agents/debrief/src/main.py --demo
```

This runs the built-in AeroCore Circuitry scenario. It does not require an LLM
API key. If no key is configured, Corvus uses deterministic demo reasoning and
still generates a complete report.

Expected result:

- blocked and at-risk work orders are identified
- findings are routed to Production, Quality Assurance, and Scheduling
- a markdown report is written to `reports/`

## 2. Run a Named Scenario

Use scenarios to show different operational modes:

```bash
python agents/debrief/src/main.py --list-scenarios
python agents/debrief/src/main.py --scenario normal
python agents/debrief/src/main.py --scenario crisis
python agents/debrief/src/main.py --scenario staffing
```

Named scenarios use the configured LLM provider unless they are run through
`--demo`.

## 3. Configure a Real Site

Edit `agents/debrief/config/onboarding.yaml` with the customer's language and
operating model:

- company and site name
- terms for build, work order, operator, or technician
- delay and stall thresholds
- shift definitions
- team names, focus areas, meetings, and routing signals

This file is how Corvus turns generic MES data into local meeting language.

## 4. Connect a CSV Export

Place the export somewhere in the repository, then run:

```bash
python agents/debrief/src/main.py --csv shared/data/manufacturing_log.csv
```

If no mapping exists, Corvus launches the CSV mapper. The mapper proposes how
customer columns map to the Corvus MES schema and saves that mapping back to
`onboarding.yaml`.

After a mapping is saved, future runs skip the LLM mapping step unless the CSV
schema changes or `--force` is used with `map_csv.py`.

For scripted checks, preview the mapping without prompts or file writes:

```bash
python agents/debrief/src/tools/map_csv.py shared/data/manufacturing_log.csv --yes --dry-run
```

## 5. Review the Report

The report contains:

- an intelligence summary
- priority findings
- recommended actions
- team-specific meeting checklists

Reports are printed to the console and saved as markdown under the configured
report output directory.

## 6. Iterate Toward Production

For a production deployment, the next work usually is:

- replace the mock API connector with the customer's MES API
- add authentication and request configuration
- add richer report export formats
- expand tests around real connector contracts
- tune onboarding thresholds and team routing after floor feedback
