import argparse
import os
import sys

# resolve all paths relative to this file's location
_THIS_FILE    = os.path.abspath(__file__)
_SRC_DIR      = os.path.dirname(_THIS_FILE)
_AGENT_ROOT   = os.path.dirname(_SRC_DIR)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))
_SHARED_DIR   = os.path.join(_PROJECT_ROOT, "shared")

sys.path.insert(0, _SRC_DIR)
sys.path.insert(0, _SHARED_DIR)
sys.path.insert(0, _PROJECT_ROOT)

from utils.config import load_config, load_onboarding
from tools.map_csv import run as run_mapper
from reporting.debrief_template import DebriefGenerator
from agents.debrief_agent import run_debrief_agent


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
        default=os.path.join(_AGENT_ROOT, "config", "onboarding.yaml"),
        help="Path to onboarding config"
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


def ensure_csv_mapping(
    csv_path: str,
    onboarding_path: str,
    onboarding: dict
) -> dict:
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

    print("[CORVUS] No column mapping found for this CSV.")
    print("[CORVUS] Running auto-mapper now...\n")
    run_mapper(csv_path, onboarding_path)
    return load_onboarding(onboarding_path)


def main():
    args = parse_args()

    if args.list_scenarios:
        print("Available scenarios: normal, crisis, staffing, acs")
        return

    config_path    = os.path.join(_AGENT_ROOT, "config", "config.yaml")
    onboarding_path = args.onboarding

    config     = load_config(config_path)
    onboarding = load_onboarding(onboarding_path)

    if args.scenario:
        config["scenario"] = args.scenario
        print(f"[CORVUS] Running scenario: {args.scenario.upper()}\n")

    elif args.csv:
        if not os.path.exists(args.csv):
            print(f"[CORVUS] CSV file not found: {args.csv}")
            sys.exit(1)
        onboarding = ensure_csv_mapping(args.csv, onboarding_path, onboarding)
        config["mes_type"] = "csv"
        config["csv_file_path"] = args.csv
        print(f"[CORVUS] Running against CSV: {args.csv}\n")

    else:
        print(f"[CORVUS] Running with mes_type: {config.get('mes_type', 'not set')}\n")

    debrief  = run_debrief_agent(config, onboarding)
    reporter = DebriefGenerator(config, onboarding)
    report   = reporter.generate(debrief)
    reporter.output(report)


if __name__ == "__main__":
    main()
