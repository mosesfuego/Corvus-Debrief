from agents.debrief_agent import run_debrief_agent
from reporting.debrief_template import DebriefGenerator
from utils.config import load_config, load_onboarding

def main():
    config = load_config()
    onboarding = load_onboarding()

    debrief = run_debrief_agent(config, onboarding)

    reporter = DebriefGenerator(config, onboarding)
    report = reporter.generate(debrief)
    reporter.output(report)

if __name__ == "__main__":
    main()
