from agents.debrief_agent import run_debrief_agent
from reporting.debrief_template import DebriefGenerator
from utils.config import load_config

def main():
    config = load_config()
    print("API KEY:", config["agents"]["api_key"][:8], "...")  # only print first 8 chars
    print("BASE URL:", config["agents"]["base_url"])
    print("MODEL:", config["agents"]["model"])
    debrief = run_debrief_agent(config)
    reporter = DebriefGenerator(config)
    reporter.output(debrief)

if __name__ == "__main__":
    main()
