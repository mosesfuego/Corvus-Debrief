import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.debrief_agent import run_debrief_agent
from reporting.debrief_template import DebriefGenerator
from utils.config import load_config, load_onboarding
from tools.map_csv import run as run_mapper


def parse_args():
    parser = argparse.ArgumentParser(description="Corvus Debrief Agent 🦅")

    parser.add_argument(
        "--scenario",
        choices=["normal", "crisis", "staffing", "acs"],
        default=None,
        help="Run a demo scenario instead of live data"
    )
    parser.add_argument(
        "--onboarding",
        default="config/onboarding.yaml",
        help="Path to onboarding config (default: config/onboarding.yaml)"
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Path to CSV file to run against"
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available demo scenarios"
    )

    return parser.parse_args()


def ensure_csv_mapping(csv_path: str, onboarding_path: str, onboarding: dict) -> dict:
    """
    Check if a valid column mapping exists for this CSV.
    If not, run the mapper automatically before proceeding.
    Returns updated onboarding dict.
    """
    csv_config = onboarding.get("csv_connector", {})
    existing_map = csv_config.get("column_map", {})

    if existing_map:
        print("[CORVUS] Column mapping found — skipping mapper.\n")
        return onboarding

    # no mapping exists — run mapper automatically
    print("[CORVUS] No column mapping found for this CSV.")
    print("[CORVUS] Running auto-mapper now...\n")

    run_mapper(csv_path, onboarding_path)

    # reload onboarding after mapper saves the mapping
    return load_onboarding(onboarding_path)


def main():
    args = parse_args()

    if args.list_scenarios:
        print("Available scenarios: normal, crisis, staffing, acs")
        return

    config = load_config()
    onboarding = load_onboarding(args.onboarding)

    # scenario flag takes priority
    if args.scenario:
        config["scenario"] = args.scenario
        print(f"[CORVUS] Running scenario: {args.scenario.upper()}\n")

    # csv flag — auto-map if needed, then run
    
    elif args.csv:
        onboarding = ensure_csv_mapping(args.csv, args.onboarding, onboarding)
        config["mes_type"] = "csv"
        config["csv_file_path"] = args.csv
        print(f"[CORVUS] Running against CSV: {args.csv}\n")

    # no flag — use mes_type from config.yaml
    else:
        print(f"[CORVUS] Running with mes_type: {config.get('mes_type', 'not set')}\n")

    debrief = run_debrief_agent(config, onboarding)

    reporter = DebriefGenerator(config, onboarding)
    report = reporter.generate(debrief)
    reporter.output(report)


if __name__ == "__main__":
    main()
