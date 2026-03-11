import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
from agents.debrief_agent import run_debrief_agent
from reporting.debrief_template import DebriefGenerator
from utils.config import load_config, load_onboarding


def parse_args():
    parser = argparse.ArgumentParser(description="Corvus Debrief Agent 🦅")
    parser.add_argument(
        "--scenario",
        choices=["normal", "crisis", "staffing"],
        default=None,
        help="Run a demo scenario instead of live data"
    )
    parser.add_argument(
        "--onboarding",
        default="config/onboarding.yaml",
        help="Path to onboarding config (default: config/onboarding.yaml)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config()
    onboarding = load_onboarding(args.onboarding)

    # inject scenario into config if flag provided
    if args.scenario:
        config["scenario"] = args.scenario
        print(f"[CORVUS] Running scenario: {args.scenario.upper()}\n")

    debrief = run_debrief_agent(config, onboarding)
    reporter = DebriefGenerator(config, onboarding)
    report = reporter.generate(debrief)
    reporter.output(report)


if __name__ == "__main__":
    main()
