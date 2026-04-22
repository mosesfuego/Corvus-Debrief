#!/bin/bash
# restructure.sh
# Corvus MFG folder restructuring script
# Run from project root: bash restructure.sh

set -e  # exit on any error

echo "🦅 Corvus MFG — restructuring project..."
echo ""

# safety check — make sure we're in the right place
if [ ! -f "README.md" ] || [ ! -d "src" ]; then
    echo "❌ Run this from the project root (where src/ and README.md live)"
    exit 1
fi

# backup first
echo "📦 Creating backup at ../corvus_backup..."
cp -r . ../corvus_backup
echo "✅ Backup created"
echo ""

# create new top-level structure
echo "📁 Creating new folder structure..."
mkdir -p agents/debrief
mkdir -p shared/utils
mkdir -p shared/memory
mkdir -p shared/data
mkdir -p shared/reports
mkdir -p shared/skills/csv_mapping
mkdir -p shared/skills/pattern_detection
mkdir -p shared/skills/team_routing
mkdir -p shared/skills/mes_connectors
mkdir -p agents/debrief/skills/debrief
echo "✅ Folders created"
echo ""

# move agent-specific folders
echo "🚚 Moving agent folders..."
mv src        agents/debrief/src
mv prompts    agents/debrief/prompts
mv config     agents/debrief/config
mv tests      agents/debrief/tests

# move scripts if it exists
if [ -d "scripts" ]; then
    mv scripts agents/debrief/scripts
fi
echo "✅ Agent folders moved"
echo ""

# move shared folders
echo "🚚 Moving shared folders..."
mv memory     shared/memory
mv data       shared/data
mv reports    shared/reports

# move utils if at root level
if [ -d "utils" ]; then
    mv utils shared/utils
fi
echo "✅ Shared folders moved"
echo ""

# create shared skill placeholders
echo "📝 Creating skill placeholders..."

cat > shared/skills/csv_mapping/SKILL.md << 'EOF'
# CSV Mapping Skill

## Purpose
Map any customer CSV to the Corvus internal schema using LLM assistance.

## When to use
- First time running against a new CSV file
- CSV structure has changed (--force flag)

## Entry point
python agents/debrief/src/tools/map_csv.py data/your_file.csv

## Key behaviors
- Auto-accepts mappings with confidence >= 0.85
- Prompts only on uncertain fields that have a candidate match
- Skips fields silently when no CSV column exists
- Preserves unknown columns as extended{} fields
- Caches mapping by header fingerprint

## Shared by
- Corvus Debrief
- (future) Corvus Yield
- (future) Corvus Supply
EOF

cat > shared/skills/pattern_detection/SKILL.md << 'EOF'
# Pattern Detection Skill

## Purpose
Identify recurring signals across runs using memory log.

## When to use
- Agent reasoning over historical context
- Identifying systemic vs one-off issues

## Entry point
shared/memory/log.json

## Key behaviors
- Last 5 runs injected into agent context
- Recurring signals flagged as systemic
- Pattern note generated when same signal appears 3+ times

## Shared by
- Corvus Debrief
- (future) all Corvus MFG agents
EOF

cat > shared/skills/team_routing/SKILL.md << 'EOF'
# Team Routing Skill

## Purpose
Route findings to the correct team based on onboarding config.

## When to use
- After signals are computed
- Before generating final report

## Configuration
agents/debrief/config/onboarding.yaml → teams section

## Key behaviors
- Routes by watch_signals match
- Routes by cares_about keyword match
- Urgency levels: normal / high / critical

## Shared by
- Corvus Debrief
- (future) all Corvus MFG agents
EOF

cat > agents/debrief/skills/debrief/SKILL.md << 'EOF'
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
EOF

echo "✅ Skill files created"
echo ""

# create agents/debrief/__init__ placeholder
touch agents/__init__.py
touch agents/debrief/__init__.py

# create top level shared readme
cat > shared/README.md << 'EOF'
# Corvus MFG — Shared Resources

This folder contains resources shared across all Corvus MFG agents.

## Structure

shared/
├── skills/              # Shared agent capabilities
│   ├── csv_mapping/     # Map any CSV to Corvus schema
│   ├── pattern_detection/ # Detect recurring signals
│   ├── team_routing/    # Route findings to teams
│   └── mes_connectors/  # Connect to MES systems
├── utils/               # Shared Python utilities
├── memory/              # Shared run history
├── data/                # Customer data files
└── reports/             # Generated reports (all agents)
EOF

echo "✅ Shared README created"
echo ""

echo "============================================"
echo "✅ Restructuring complete."
echo ""
echo "New structure:"
echo ""
echo "corvus-mfg/"
echo "├── agents/"
echo "│   └── debrief/          ← Corvus Debrief agent"
echo "│       ├── src/"
echo "│       ├── config/"
echo "│       ├── prompts/"
echo "│       ├── tests/"
echo "│       └── skills/"
echo "├── shared/"
echo "│   ├── skills/"
echo "│   ├── utils/"
echo "│   ├── memory/"
echo "│   ├── data/"
echo "│   └── reports/"
echo "├── .env"
echo "├── requirements.txt"
echo "└── README.md"
echo ""
echo "⚠️  NEXT STEPS — paths need updating:"
echo ""
echo "1. Update sys.path inserts in:"
echo "   agents/debrief/src/main.py"
echo "   agents/debrief/src/tools/map_csv.py"
echo ""
echo "2. Update config paths in:"
echo "   agents/debrief/src/utils/config.py"
echo "   agents/debrief/src/agents/debrief_agent.py"
echo ""
echo "3. Update memory path in:"
echo "   shared/memory/memory.py  (if exists)"
echo ""
echo "4. Run tests:"
echo "   cd agents/debrief && pytest tests/ -v"
echo ""
echo "5. Test full run:"
echo "   python agents/debrief/src/main.py --scenario normal"
echo ""
echo "Backup is at: ../corvus_backup"
echo "============================================"