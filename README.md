# Corvus Debrief 🦅

> *"Turn manufacturing chaos into actionable intelligence."*

Corvus Debrief is an AI agent that connects to your Manufacturing Execution System (MES), reasons over live build data, and automatically generates meeting-ready debrief reports — routed to the right teams, in your language, before your morning standup.

---

## What It Does

You run one command. Corvus:

1. Pulls current build data from your MES or CSV export
2. Maps your data schema automatically using LLM assistance
3. Identifies what is blocked, at risk, or needs a human decision
4. Routes findings to the right teams automatically
5. Generates a structured debrief report ready for your meeting

No dashboards to interpret. No data to manually compile. Just intelligence, delivered.

---

## Quick Start

From the repository root:

```bash
# Run against your own CSV
python agents/debrief/src/main.py --csv shared/data/your_export.csv

# Demo scenarios
python agents/debrief/src/main.py --scenario normal
python agents/debrief/src/main.py --scenario crisis
python agents/debrief/src/main.py --scenario staffing

# See available scenarios
python agents/debrief/src/main.py --list-scenarios
```

Reports are printed to console and saved to `reports/`.

---

## Setup in Under 2 Hours

### Prerequisites
- Python 3.10+
- An LLM API key (NVIDIA NIM, OpenAI, or compatible)

### Installation

```bash
git clone https://github.com/yourusername/corvus-debrief.git
cd corvus-debrief

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

**Step 1 — Set your API key:**

Create a `.env` file at project root:
```
NIM_API_KEY=your_api_key_here
```

**Step 2 — Configure your system:**

Edit `agents/debrief/config/config.yaml`:
```yaml
mes_type: "csv"

agents:
  provider: "nim"
  model: "moonshotai/kimi-k2.5"
  api_key: ${NIM_API_KEY}
  base_url: "https://integrate.api.nvidia.com/v1"

reporting:
  output_dir: "./reports"
  format: "console"
```

**Step 3 — Tell Corvus about your operation:**

Edit `agents/debrief/config/onboarding.yaml`:
```yaml
schema_version: "1.0"
company: "Your Company"
site: "Plant A"

terminology:
  build: "workorder"
  operator: "technician"

thresholds:
  delay_minutes: 120
  stall_minutes: 45

shifts:
  - name: "Day Shift"
    start: "07:00"
    end: "15:00"
  - name: "Night Shift"
    start: "15:00"
    end: "23:00"

teams:
  - name: "Quality Assurance"
    cares_about:
      - "blocked builds"
      - "inspection backlog"
      - "yield issues"
    watch_signals:
      - stalled_build
      - paused_build
    alert_recipients:
      - role: "QA Manager"
    meeting: "Daily Quality Standup — 8:00am"

  - name: "Production"
    cares_about:
      - "on-time delivery"
      - "bottlenecks"
      - "overtime decisions"
    watch_signals:
      - delayed_build
      - stalled_build
    alert_recipients:
      - role: "Production Supervisor"
    meeting: "Morning Production Review — 7:30am"

  - name: "Scheduling"
    cares_about:
      - "staffing gaps"
      - "shift coverage"
      - "unassigned operator"
    watch_signals:
      - delayed_build
    alert_recipients:
      - role: "Scheduler"
    meeting: "Weekly Planning — Monday 9:00am"
```

**Step 4 — Drop your CSV and run:**

```bash
python agents/debrief/src/main.py --csv shared/data/your_export.csv
```

If this is the first time running against this CSV, Corvus will automatically map your columns.

---

## CSV Column Mapping

Corvus accepts any CSV — no specific column names required.

On first run against a new CSV, Corvus uses an LLM to propose a column mapping:

```bash
# Auto-mapping happens automatically when you pass --csv
python agents/debrief/src/main.py --csv shared/data/your_export.csv

# Or run the mapper manually
python agents/debrief/src/tools/map_csv.py shared/data/your_export.csv

# Force remap if your CSV structure changed
python agents/debrief/src/tools/map_csv.py shared/data/your_export.csv --force
```

**What the mapper does:**
- Auto-accepts high confidence matches (>=85%)
- Prompts you only on uncertain fields that have a candidate match
- Skips fields silently when no CSV column exists for them
- Saves mapping to onboarding.yaml
- Caches by header fingerprint — never remaps unless schema changes
- Unknown columns are preserved as extended fields — the agent sees everything

**Example mapping session:**
```
AUTO-ACCEPTED:
  build_id     <- 'Job_ID' (95%)
  station_id   <- 'Work_Center' (90%)
  operator_id  <- 'Operator_ID' (95%)
  status       <- 'Status' (90%)
  notes        <- 'Comments' (85%)

NEEDS YOUR REVIEW:
  start_time   <- 'Timestamp' (70% confidence)
  Accept? Press Enter or type correct column name:

UNMAPPED COLUMNS (passed through as extended):
  Line_ID, Customer_Tier, Error_Code, Part_Number, Yield_Rate
```

---

## How Extended Fields Work

Any CSV column that does not map to the Corvus schema is automatically preserved as an extended field on each build:

```python
{
    "build_id":   "ACS-2241",
    "station_id": "SMT_SIPLACE_B",
    "status":     "Blocked",
    "extended": {
        "Customer_Tier": "Tier 1 (Aero)",
        "Error_Code":    "ERR_FEED_MISMATCH",
        "Part_Number":   "R0603-10K",
        "Yield_Rate":    "0.82"
    }
}
```

The agent reasons over extended fields automatically — no additional configuration needed.

---

## Sample Output

```
============================================================
CORVUS DEBRIEF REPORT
AeroCore Circuitry — Plant A
2026-03-26 | 07:28
============================================================

SUMMARY
The factory floor has 2 builds completely stopped. Line 3 is
down on a Tier 1 Aerospace job due to expired operator
certification and a recurring feeder mismatch (3rd occurrence).
Line 5 is blocked on material shortage awaiting QA approval.

PRIORITY FINDINGS
Blocked: ACS-2241 on SMT_SIPLACE_B — operator cert expired
         for Aero Medical, feeder position 22 mismatch,
         3rd occurrence of Kitting process gap.
         ACS-2198 on Kitting — C0402-100V shortage,
         broker buy substitution pending QA approval 2+ hrs.

At Risk: None.

Needs Decision: QA approval required for broker buy.
                Operator recertification needed to restore
                Tier 1 production.

Pattern Note: ERR_FEED_MISMATCH at feeder position 22
              is 3rd occurrence — systematic Kitting gap,
              not operator error.

RECOMMENDED ACTIONS
- Escalate operator cert renewal for Aero Medical -> Production
- Fix Kitting process gap on Line 3 -> Production
- Expedite QA review of broker buy C0402-100V -> Quality Assurance
- Evaluate Line 5 schedule impact -> Scheduling
```

---

## Architecture

```
Any CSV / MES / SQLite
        |
   CSV Mapper (LLM-assisted, fingerprint cached)
        |
   CSVMESConnector
   (known fields -> schema, unknown -> extended{})
        |
   Analytics Engine
   (enriches builds with signals)
        |
   Debrief Agent
   (think -> tool -> observe -> think loop)
        |
   Report Generator
   (routes findings to teams)
        |
   Console + reports/
```

### Key Files

| File | Purpose |
|------|---------|
| `agents/debrief/src/main.py` | Entry point, CLI |
| `agents/debrief/src/agents/debrief_agent.py` | Agent reasoning loop |
| `agents/debrief/src/agents/tools.py` | Tools the agent can call |
| `agents/debrief/src/tools/map_csv.py` | LLM-assisted CSV column mapper |
| `agents/debrief/src/connectors/csv_connector.py` | Flexible CSV connector |
| `agents/debrief/src/connectors/factory.py` | Connector selector with caching |
| `agents/debrief/src/analytics/build_metrics.py` | Enriches raw build data |
| `agents/debrief/src/reporting/debrief_template.py` | Report formatter |
| `agents/debrief/config/onboarding.yaml` | Your operation profile |
| `agents/debrief/config/config.yaml` | System configuration |
| `agents/debrief/prompts/system_prompt.txt` | Agent reasoning instructions |
| `shared/memory/log.json` | Run history for pattern detection |

---

## CLI Reference

```bash
# Run against CSV (auto-maps on first run)
python agents/debrief/src/main.py --csv shared/data/your_file.csv

# Use a specific onboarding config
python agents/debrief/src/main.py --csv shared/data/your_file.csv --onboarding agents/debrief/config/acs_onboarding.yaml

# Open the local onboarding wizard and update onboarding.yaml
python agents/debrief/src/main.py --onboard_wizard

# Demo scenarios
python agents/debrief/src/main.py --scenario normal
python agents/debrief/src/main.py --scenario crisis
python agents/debrief/src/main.py --scenario staffing

# List scenarios
python agents/debrief/src/main.py --list-scenarios

# Map CSV manually
python agents/debrief/src/tools/map_csv.py shared/data/your_file.csv

# Force remap
python agents/debrief/src/tools/map_csv.py shared/data/your_file.csv --force

# Map with specific onboarding
python agents/debrief/src/tools/map_csv.py shared/data/your_file.csv --onboarding agents/debrief/config/acs_onboarding.yaml
```

---

## Running Tests

```bash
# Setup test database first (from repository root)
python agents/debrief/tests/setup_test_db.py

# Run all tests
pytest agents/debrief/tests/ -v

# Run with coverage
pytest agents/debrief/tests/ -v --cov=agents/debrief/src --cov-report=term-missing
```

---

## Supported Connectors

| Type | Config Value | Status |
|------|-------------|--------|
| Any CSV (auto-mapped) | `csv` | Ready |
| SQLite database | `sqlite` | Ready |
| REST API | `api` | Ready |
| Demo scenarios | `--scenario` flag | Ready |
| SAP / ERP | coming soon | Roadmap |
| Real-time streaming | coming soon | Roadmap |

---

## Agent Memory

Corvus maintains a rolling log of past runs in `shared/memory/log.json`. The last 5 runs are injected into the agent context so it can identify patterns across shifts:

"WELD-01 has been blocked three consecutive shifts — this is systemic, not a one-off."

---

## Roadmap

- [ ] Job tier escalation rules (Phase 4.5B)
- [ ] LLM-assisted extended field suggestions in mapper (Phase 4.5C)
- [ ] Email delivery of reports before each meeting
- [ ] Slack / Teams integration for critical flags
- [ ] ERP / MRP connectors (SAP, Oracle)
- [ ] Web dashboard for report history
- [ ] Multi-site comparison
- [ ] Docker container for self-hosted deployment

---

## Project Structure

```
corvus-mfg/
├── agents/
│   └── debrief/
│       ├── config/
│       │   ├── config.yaml
│       │   └── onboarding.yaml
│       ├── prompts/
│       │   └── system_prompt.txt
│       ├── skills/
│       ├── tests/
│       └── src/
│           ├── main.py
│           ├── agents/
│           ├── analytics/
│           ├── connectors/
│           ├── memory/
│           ├── reporting/
│           └── tools/
├── shared/
│   ├── utils/
│   ├── memory/
│   ├── data/
│   ├── reports/
│   └── skills/
├── .env
├── requirements.txt
└── README.md
```

---

## Contributing

1. Fork and branch: `git checkout -b feature/my-feature`
2. Write tests for new functionality
3. Ensure tests pass: `pytest agents/debrief/tests/ -v`
4. Submit PR with clear description

---

## License

MIT 2026 Corvus Debrief Contributors

---

*Built for the operators, engineers, and managers who deserve better than staring at a screen full of raw MES data before their 7:30am meeting.*
