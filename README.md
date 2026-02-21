# Corvus Debrief 🦅

> *"Turn manufacturing chaos into actionable intelligence."*

Corvus Debrief is an AI-powered analytics and reporting system for manufacturing builds. It connects to MES (Manufacturing Execution Systems), analyzes build metrics, identifies patterns, and auto-generates intelligent debrief reports with recommendations.

---

## What It Does

- 🔌 **Connects** to manufacturing data sources (MES, databases, logs)
- 📊 **Analyzes** build metrics, failure patterns, and performance trends
- 🤖 **Intelligently debriefs** using AI agents to identify root causes
- 📄 **Generates** executive summaries, detailed reports, and action items
- 🔄 **Integrates** with CI/CD pipelines for automated post-build analysis

---

## Architecture Overview

```
corvus-debrief/
├── src/
│   ├── connectors/          # MES, API, and data source adapters
│   ├── analytics/           # Metrics calculation & trend analysis
│   ├── agents/              # LLM-powered debrief reasoning
│   └── reporting/           # Report templates & output generation
├── config/                  # YAML configs for connectors & thresholds
├── docs/                    # Architecture & user documentation
├── tests/                   # Unit & integration tests
└── scripts/                 # Utility scripts (data seeding, etc.)
```

### Data Flow

```
MES / Build DB → Connectors → Analytics Engine → Debrief Agent → Reports
                                    ↓
                              Thresholds & Alerts
                                    ↓
                              CI/CD Notifications
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- (Optional) MES database credentials
- (Optional) LLM API key (OpenAI/Anthropic/OpenRouter)

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

# Configure (copy template and edit)
cp config/config.yaml config/config.local.yaml
# Edit config.local.yaml with your credentials

# Run with sample data
python scripts/seed_sample_data.py
python src/main.py --demo
```

### Running Tests

```bash
pytest tests/ -v
```

---

## Configuration

Create `config/config.local.yaml` for local overrides:

```yaml
mes:
  endpoint: "https://your-mes.internal/api"
  api_key: ${MES_API_KEY}  # Set via env var

analytics:
  thresholds:
    yield_warning: 0.85
    yield_critical: 0.70
    cycle_time_variance: 0.15

agents:
  completion:
    provider: "openai"  # or "anthropic", "openrouter"
    model: "gpt-4"
    api_key: ${OPENAI_API_KEY}

reporting:
  output_dir: "./reports"
  formats: ["markdown", "json"]
```

---

## Usage Examples

### Generate a Build Debrief

```python
from src.connectors.mes_simulation import MESConnector
from src.analytics.build_metrics import BuildAnalyzer
from src.agents.debrief_agent import DebriefAgent
from src.reporting.debrief_template import ReportGenerator

# Initialize components
mes = MESConnector(config_path="config/config.yaml")
analyzer = BuildAnalyzer()
agent = DebriefAgent()
reporter = ReportGenerator()

# Fetch and analyze build data
builds = mes.get_builds(since="24h")
metrics = analyzer.calculate(builds)
insights = agent.debrief(metrics)
report = reporter.generate(metrics, insights, format="markdown")

print(report)
```

### CLI Usage

```bash
# Debrief last 24 hours
python src/main.py --since 24h --output reports/

# Debrief specific date range
python src/main.py --from 2024-01-15 --to 2024-01-20

# Export JSON only
python src/main.py --since 24h --format json --no-markdown
```

---

## Project Structure Details

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| `connectors` | Data ingestion | `mes_simulation.py` |
| `analytics` | Metrics & analysis | `build_metrics.py` |
| `agents` | AI reasoning | `debrief_agent.py` |
| `reporting` | Output generation | `debrief_template.py` |

---

## Roadmap

- [ ] Real-time MES streaming connector
- [ ] Slack/Teams integration for alerts
- [ ] Dashboard UI (React-based)
- [ ] Multi-site comparison analytics
- [ ] Predictive failure modeling

---

## Contributing

1. Fork and branch: `git checkout -b feature/my-feature`
2. Write tests for new functionality
3. Ensure CI passes: `pytest && flake8`
4. Submit PR with clear description

---

## License

MIT © 2024 Corvus Debrief Contributors

---

## Support

- 📖 Docs: `docs/`
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

*Built with Python, curiosity, and a desire to make manufacturing data actually useful.*
