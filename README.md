# Corvus Debrief 🦅

> *"Turn manufacturing chaos into actionable intelligence."*

Corvus Debrief is an AI agent that connects to your Manufacturing Execution System (MES), reasons over live build data, and automatically generates meeting-ready debrief reports — routed to the right teams, in your language, before your morning standup.

---

## What It Does

You run one command. Corvus:

1. Pulls current build data from your MES
2. Identifies what is blocked, at risk, or needs a human decision
3. Routes findings to the right teams automatically
4. Generates a structured debrief report ready for your meeting

No dashboards to interpret. No data to manually compile. Just intelligence, delivered.

---

## Quick Demo

```bash
# See a healthy factory floor
python src/main.py --scenario normal

# See a crisis — multiple blocks, missed deadlines
python src/main.py --scenario crisis

# See a staffing disaster
python src/main.py --scenario staffing

# Run against your real MES data
python src/main.py
```

Reports are printed to console and saved to `reports/`.

---

## Setup in Under 2 Hours

### Prerequisites
- Python 3.10+
- An LLM API key (NVIDIA NIM, OpenAI, or Anthropic)
- Optional: MES database credentials

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/corvus-debrief.git
cd corvus-debrief

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

**Step 1 — Set your API key:**

Create a `.env` file at project root:
```
NIM_API_KEY=your_api_key_here
```

**Step 2 — Tell Corvus about your operation:**

Edit `config/onboarding.yaml`:

```yaml
company: "Your Company"
site: "Plant A"

terminology:
  build: "workorder"       # what you call a build
  operator: "technician"   # what you call an operator

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

**Step 3 — Point Corvus at your MES:**

Edit `config/config.yaml`:

```yaml
mes_type: "csv"    # "csv" | "sqlite" | "api"

agents:
  provider: "nim"
  model: "moonshotai/kimi-k2.5"
  api_key: ${NIM_API_KEY}
  base_url: "https://integrate.api.nvidia.com/v1"
```

**Step 4 — Run it:**

```bash
python src/main.py
```

That's it. Corvus will pull your data, reason over it, and produce a meeting-ready report.

---

## Sample Output

```
============================================================
🦅  CORVUS DEBRIEF REPORT
    Acme Manufacturing — Plant A
    2026-03-16 | 07:30
============================================================

INTELLIGENCE SUMMARY
------------------------------------------------------------
SUMMARY
Assembly and welding stations are completely stopped this morning,
with three additional work orders falling behind schedule.
This cluster of issues needs immediate attention.

PRIORITY FINDINGS
🔴 Blocked: ASSEMBLY-A1 (conveyor fault, no ETA) and WELD-01
            (awaiting QA sign-off on weld deviation)
🟡 At Risk: Four work orders will miss deadlines if nothing changes
🔵 Needs Decision: QA must approve or reject weld deviation
                   within 30 minutes
⚪ Pattern Note: Independent issues hitting simultaneously —
                not systemic, but floor is at capacity

RECOMMENDED ACTIONS
- Escalate conveyor repair ETA → Production
- Prioritize QA weld review — 30 min window → Quality Assurance
- Assign operator to INSPECT-01 before 12:00 → Scheduling

============================================================
MEETING CHECKLISTS BY TEAM
============================================================

📋  QUALITY ASSURANCE
    Daily Quality Standup — 8:00am
    Notify: QA Manager

    Action items from this debrief:
      - Prioritize QA review of weld deviation → Quality Assurance

------------------------------------------------------------

📋  PRODUCTION
    Morning Production Review — 7:30am
    Notify: Production Supervisor

    Action items from this debrief:
      - Escalate conveyor repair ETA → Production
      - Confirm paint supply delivery window → Production

------------------------------------------------------------
```

---

## Architecture

```
MES / CSV / SQLite
       ↓
   Connectors
       ↓
 Analytics Engine      ← enriches builds with signals
       ↓
  Debrief Agent        ← LLM reasoning loop
  (think→tool→observe→think)
       ↓
 Report Generator      ← routes findings to teams
       ↓
 Console + Reports/
```

### Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Entry point, CLI |
| `src/agents/debrief_agent.py` | Agent reasoning loop |
| `src/agents/tools.py` | Tools the agent can call |
| `src/analytics/build_metrics.py` | Enriches raw build data |
| `src/connectors/factory.py` | Connector selector |
| `src/reporting/debrief_template.py` | Report formatter |
| `config/onboarding.yaml` | Your operation profile |
| `config/config.yaml` | System configuration |
| `prompts/system_prompt.txt` | Agent reasoning instructions |

---

## Running Tests

```bash
# Setup test database first
python tests/setup_test_db.py

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Supported MES Connectors

| Type | Config Value | Status |
|------|-------------|--------|
| CSV export | `csv` | ✅ Ready |
| SQLite database | `sqlite` | ✅ Ready |
| REST API | `api` | ✅ Ready |
| SAP / ERP | coming soon | 🔄 Roadmap |
| Real-time streaming | coming soon | 🔄 Roadmap |

---

## Roadmap

- [ ] Email delivery of reports before each meeting
- [ ] Slack / Teams integration for critical flags
- [ ] ERP / MRP connectors (SAP, Oracle)
- [ ] Real-time MES streaming
- [ ] Web dashboard for report history
- [ ] Multi-site comparison

---

## Contributing

1. Fork and branch: `git checkout -b feature/my-feature`
2. Write tests for new functionality
3. Ensure tests pass: `pytest tests/ -v`
4. Submit PR with clear description

---

## License

MIT © 2026 Corvus Debrief Contributors

---

*Built for the operators, engineers, and managers who deserve better than
staring at a screen full of raw MES data before their 7:30am meeting.*
