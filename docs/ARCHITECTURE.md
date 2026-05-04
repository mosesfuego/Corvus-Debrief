# Corvus Debrief Architecture

Corvus Debrief is a command-line manufacturing debrief agent. It connects to a
data source, normalizes work order records, computes deterministic production
signals, lets an LLM reason over those facts, then writes a meeting-ready report.

## Runtime Flow

1. `agents/debrief/src/main.py` parses CLI flags and loads configuration.
2. `shared/utils/config.py` loads `config.yaml`, `.env`, and `onboarding.yaml`.
3. `connectors/factory.py` selects the data connector:
   - scenario connector for demo data
   - CSV connector for mapped customer exports
   - SQLite connector for local MES-style databases
   - API connector placeholder for future HTTP-backed MES integrations
4. `intake/` classifies sources, stores mapping metadata, and shares schema
   mapping helpers across CSV/API/database intake.
5. `canonical/` defines normalized manufacturing records such as work orders,
   operations, quality issues, material status, and labor assignments.
6. `orchestration/debrief_orchestrator.py` runs domain agents over connector
   data and builds a compact debrief context.
7. `domain_agents/work_order_agent.py` enriches builds with deterministic
   signals such as blocked, delayed, stalled, at-risk, unassigned, and needs
   decision. Lightweight quality/material agents extract early cross-domain
   signals from notes and extended fields.
8. `agents/debrief_agent.py` exposes those facts as LLM tools and asks the
   model for a debrief.
9. `reporting/debrief_template.py` wraps the debrief in a standard report and
   extracts routed action items for each configured team.
10. `memory/memory.py` stores a rolling run history in `shared/memory/log.json`.

## Important Boundaries

The analytics layer should produce reproducible facts. The LLM should explain,
prioritize, and route those facts rather than inventing raw metrics.

Connectors should return the same MES schema:

- `build_id`
- `station_id`
- `operator_id`
- `start_time`
- `planned_end`
- `needed_by_date`
- `target_quantity`
- `completed_quantity`
- `labor_hours`
- `status`
- `notes`

CSV inputs may include arbitrary extra columns. Those fields are preserved under
`build["extended"]` so the agent can reason over customer-specific context
without requiring schema changes.

## Package Shape

```text
connectors/
  csv_connector.py
  api_connector.py
  sqlite_connector.py

intake/
  source_classifier.py
  mapping_registry.py
  schema_mapper.py

canonical/
  work_order.py
  operation.py
  quality_issue.py
  material_status.py
  labor_assignment.py

domain_agents/
  work_order_agent.py
  quality_lite_agent.py
  materials_lite_agent.py

orchestration/
  debrief_orchestrator.py

reporting/
  debrief_template.py
```

The architectural rule is: connectors fetch raw data, intake maps/classifies
that data, canonical models define stable records, domain agents produce compact
findings, and the debrief orchestrator coordinates the flow.

## Configuration

`agents/debrief/config/config.yaml` controls runtime behavior: data source,
agent provider/model, and report output.

`agents/debrief/config/onboarding.yaml` captures customer context: company,
site, team routing, terminology, thresholds, and CSV mapping.

Environment placeholders such as `${NIM_API_KEY}` resolve from `.env` or the
process environment. Missing API keys are allowed during config load so local
demo and non-LLM tests can run; the agent raises a clear error only when a real
LLM call is required.

## Extension Points

Add a new MES source by implementing `BaseMESConnector` and registering it in
`connectors/factory.py`.

Add a new intake type by extending `intake/mapping_registry.py`, then teaching
`source_classifier.py` and `schema_mapper.py` how to recognize/map it.

Add a deeper business domain by creating a domain agent that returns:

- `domain`
- `summary`
- `findings`
- compact evidence references

Add a new demo by creating a scenario connector in
`connectors/scenarios/` and adding it to `SCENARIOS`.

Add a new report format by extending `DebriefGenerator.output`.
