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
from utils.tenants import get_tenant_context, list_tenants
from tools.map_csv import run as run_mapper
from reporting.debrief_template import DebriefGenerator
from agents.debrief_agent import run_debrief_agent
from agents.tools import get_build_metrics
from memory.memory import save_run


def parse_args():
    parser = argparse.ArgumentParser(description="Corvus Debrief Agent 🦅")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the built-in ACS demo with no config or CSV setup"
    )
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
        "--tenant",
        default=None,
        help="Load a customer profile from shared/tenants/<tenant>/onboarding.yaml"
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available demo scenarios"
    )
    parser.add_argument(
        "--list-tenants",
        action="store_true",
        help="List local tenant profiles"
    )
    return parser.parse_args()


def build_demo_config() -> dict:
    """Return a self-contained config for the built-in demo path."""
    return {
        "_demo": True,
        "mes_type": "scenario",
        "scenario": "acs",
        "agents": {
            "provider": os.environ.get("CORVUS_DEMO_PROVIDER", "nim"),
            "model": os.environ.get("CORVUS_DEMO_MODEL", "moonshotai/kimi-k2.5"),
            "api_key": (
                os.environ.get("NIM_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or ""
            ),
            "base_url": os.environ.get(
                "CORVUS_DEMO_BASE_URL",
                "https://integrate.api.nvidia.com/v1"
            ),
        },
        "reporting": {
            "output_dir": "./reports",
            "format": "console",
        },
    }


def build_demo_onboarding() -> dict:
    """Return an onboarding profile without reading onboarding.yaml."""
    return {
        "schema_version": "1.0",
        "company": "Corvus Demo — AeroCore Circuitry",
        "site": "Plant A",
        "terminology": {
            "build": "work order",
            "operator": "operator",
        },
        "thresholds": {
            "delay_minutes": 30,
            "stall_minutes": 20,
        },
        "shifts": [
            {"name": "Day Shift", "start": "06:00", "end": "14:00"},
            {"name": "Swing Shift", "start": "14:00", "end": "22:00"},
            {"name": "Night Shift", "start": "22:00", "end": "06:00"},
        ],
        "teams": [
            {
                "name": "Production",
                "cares_about": [
                    "blocked builds",
                    "SMT line bottlenecks",
                    "certification gaps",
                    "on-time delivery",
                ],
                "watch_signals": [
                    "stalled_build",
                    "paused_build",
                    "delayed_build",
                ],
                "meeting": "Morning Production Review — 7:30am",
            },
            {
                "name": "Quality Assurance",
                "cares_about": [
                    "QA holds",
                    "broker buy approvals",
                    "aerospace customer risk",
                    "yield issues",
                ],
                "watch_signals": [
                    "stalled_build",
                    "paused_build",
                    "delayed_build",
                ],
                "meeting": "Daily Quality Standup — 8:00am",
            },
            {
                "name": "Scheduling",
                "cares_about": [
                    "staffing gaps",
                    "shift coverage",
                    "unassigned operator",
                    "quick-turn priority conflicts",
                ],
                "watch_signals": [
                    "delayed_build",
                    "unassigned_operator",
                ],
                "meeting": "Daily Schedule Sync — 8:15am",
            },
        ],
    }


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
        print("[CORVUS] Available scenarios: normal, crisis, staffing, acs")
        return

    if args.list_tenants:
        tenants = list_tenants()
        if tenants:
            print("[CORVUS] Available tenants: " + ", ".join(tenants))
        else:
            print("[CORVUS] No local tenant profiles found.")
        return

    if args.demo:
        config = build_demo_config()
        onboarding = build_demo_onboarding()
        print("[CORVUS] Running built-in demo: ACS / AeroCore Circuitry\n")

    else:
        config_path    = os.path.join(_AGENT_ROOT, "config", "config.yaml")
        tenant_context = None
        onboarding_path = args.onboarding

        if args.tenant:
            tenant_context = get_tenant_context(args.tenant)
            onboarding_path = tenant_context["onboarding_path"]

        config     = load_config(config_path)
        onboarding = load_onboarding(onboarding_path)

        if tenant_context:
            config["_tenant"] = tenant_context
            config.setdefault("reporting", {})["output_dir"] = tenant_context["reports_dir"]
            print(f"[CORVUS] Tenant profile: {tenant_context['slug']}")

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

    debrief = run_debrief_agent(config, onboarding)
    reporter = DebriefGenerator(config, onboarding)
    report = reporter.generate(debrief)
    reporter.output(report)

    try:
        bundle = get_build_metrics(config, onboarding)
        save_run(config.get("_flags", []), bundle.get("builds", []), config=config)
    except Exception as exc:
        print(f"[CORVUS] Memory log not updated: {exc}")


if __name__ == "__main__":
    main()
