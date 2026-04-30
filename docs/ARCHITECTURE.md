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
4. `analytics/build_metrics.py` enriches builds with deterministic metrics and
   signals such as blocked, delayed, stalled, at-risk, unassigned, and needs
   decision.
5. `agents/debrief_agent.py` exposes those facts as LLM tools and asks the
   model for a debrief.
6. `reporting/debrief_template.py` wraps the debrief in a standard report and
   extracts routed action items for each configured team.
7. `memory/memory.py` stores a rolling run history in `shared/memory/log.json`.

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

Add a new demo by creating a scenario connector in
`connectors/scenarios/` and adding it to `SCENARIOS`.

Add a new report format by extending `DebriefGenerator.output`.
