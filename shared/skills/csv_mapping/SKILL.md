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
