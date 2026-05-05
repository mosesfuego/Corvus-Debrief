# Corvus Debrief Architecture Flow

This flow shows the current Corvus Debrief architecture after the intake,
canonical record, domain agent, and orchestration layers were added.

```mermaid
flowchart TD
    %% Sources
    subgraph S["Data Sources"]
        CSV["MES CSV Export"]
        SCENARIO["Built-in Scenario Data"]
        SQLITE["SQLite MES Database"]
        API["API Connector<br/>(mock/placeholder today)"]
    end

    %% Connector layer
    subgraph C["Connector Layer"]
        FACTORY["connectors/factory.py<br/>select connector by config"]
        CSV_CONN["csv_connector.py<br/>read mapped CSV rows"]
        SQLITE_CONN["sqlite_connector.py<br/>query MES-style tables"]
        API_CONN["api_connector.py<br/>return API-shaped MES rows"]
        SCENARIO_CONN["connectors/scenarios/*<br/>demo floor data"]
    end

    %% Intake layer
    subgraph I["Intake Layer"]
        CLASSIFIER["source_classifier.py<br/>classify data source type"]
        REGISTRY["mapping_registry.py<br/>canonical fields, aliases, source metadata"]
        MAPPER["schema_mapper.py<br/>deterministic header mapping + validation"]
        MAP_CSV["tools/map_csv.py<br/>CSV workflow, LLM fallback, fingerprint cache"]
        ONBOARDING["onboarding.yaml<br/>customer context + saved CSV mapping"]
    end

    %% Canonical layer
    subgraph K["Canonical Records"]
        WO_CANON["WorkOrder<br/>implemented and active"]
        OP_CANON["Operation<br/>defined for future routing data"]
        Q_CANON["QualityIssue<br/>defined for future QMS/NCR data"]
        MAT_CANON["MaterialStatus<br/>defined for future materials/kitting data"]
        LAB_CANON["LaborAssignment<br/>defined for future staffing data"]
    end

    %% Domain agent layer
    subgraph D["Domain Agents"]
        WO_AGENT["work_order_agent.py<br/>normalizes work orders, computes production signals"]
        Q_AGENT["quality_lite_agent.py<br/>detects quality signals from notes/extended fields"]
        MAT_AGENT["materials_lite_agent.py<br/>detects material/kitting signals from notes/extended fields"]
    end

    %% Orchestration and reasoning
    subgraph O["Orchestration + Reasoning"]
        ORCH["debrief_orchestrator.py<br/>runs connector + domain agents, builds compact context"]
        TOOLS["agents/tools.py<br/>LLM-callable tool functions"]
        LLM["debrief_agent.py<br/>LLM reasoning loop"]
    end

    %% Reporting and memory
    subgraph R["Output Layer"]
        REPORT["reporting/debrief_template.py<br/>meeting-ready markdown report"]
        CONSOLE["Console Output"]
        FILES["reports/<br/>saved markdown reports"]
        MEMORY["shared/memory/log.json<br/>rolling run history"]
    end

    %% Source to connector
    CSV --> FACTORY
    SQLITE --> FACTORY
    API --> FACTORY
    SCENARIO --> FACTORY
    FACTORY --> CSV_CONN
    FACTORY --> SQLITE_CONN
    FACTORY --> API_CONN
    FACTORY --> SCENARIO_CONN

    %% CSV mapping/intake path
    CSV -. "first run or schema changed" .-> MAP_CSV
    MAP_CSV --> CLASSIFIER
    MAP_CSV --> REGISTRY
    MAP_CSV --> MAPPER
    MAPPER --> ONBOARDING
    ONBOARDING --> CSV_CONN

    %% Connector output to canonical/domain
    CSV_CONN --> ORCH
    SQLITE_CONN --> ORCH
    API_CONN --> ORCH
    SCENARIO_CONN --> ORCH

    ORCH --> WO_AGENT
    WO_AGENT --> WO_CANON
    WO_AGENT --> Q_AGENT
    WO_AGENT --> MAT_AGENT
    Q_AGENT -. "uses signals from work-order notes/extended fields today" .-> Q_CANON
    MAT_AGENT -. "uses signals from work-order notes/extended fields today" .-> MAT_CANON

    OP_CANON -. "future routing/operation intake" .-> ORCH
    LAB_CANON -. "future labor/staffing intake" .-> ORCH

    %% Context and output
    WO_AGENT --> ORCH
    Q_AGENT --> ORCH
    MAT_AGENT --> ORCH
    ORCH --> TOOLS
    TOOLS --> LLM
    LLM --> REPORT
    REPORT --> CONSOLE
    REPORT --> FILES
    ORCH --> MEMORY
```

## Current Runtime Path

1. `main.py` loads config and onboarding context.
2. `connectors/factory.py` selects the configured data source.
3. CSV sources use `map_csv.py` when no valid mapping exists.
4. `map_csv.py` classifies the source, uses registry aliases, validates required
   fields, and saves mappings to `onboarding.yaml`.
5. The connector returns work-order-shaped records.
6. `DebriefOrchestrator` passes records through the Work Order Agent.
7. The Work Order Agent normalizes records into `WorkOrder` and computes
   deterministic production signals.
8. Quality Lite and Materials Lite agents extract early cross-domain findings
   from notes and extended fields.
9. `agents/tools.py` exposes the orchestrated context to the LLM.
10. `debrief_agent.py` creates the final debrief.
11. `DebriefGenerator` prints and saves the report.
12. Memory stores a compact run history.

## Intentional Boundaries

- Connectors fetch raw data.
- Intake classifies and maps raw source fields.
- Canonical records define stable manufacturing concepts.
- Domain agents produce scoped findings and evidence.
- The orchestrator keeps LLM context compact.
- Reporting turns findings into meeting-ready output.

## Extension Points

The architecture is ready for deeper agents later, but they are not fully
implemented yet:

- Operation/routing intake can feed `Operation`.
- QMS/NCR/inspection intake can feed `QualityIssue`.
- Inventory/kitting intake can feed `MaterialStatus`.
- Labor/shift/certification intake can feed `LaborAssignment`.
- API polling can use the same intake and canonical layers once real partner
  APIs are available.
