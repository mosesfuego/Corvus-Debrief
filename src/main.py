import sys
import os

# Adds the root directory (one level up from src) to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from connectors.factory import get_connector
from analytics.build_metrics import BuildMetrics
from reporting.debrief_template import DebriefGenerator
from utils.config import load_config

def main():
    config = load_config()
    
    connector = get_connector(config)
    analytics_engine = BuildMetrics(config)
    reporter = DebriefGenerator(config)

    builds = connector.fetch_builds()
    analyzed_builds = analytics_engine.evaluate(builds)
    debrief = reporter.generate(analyzed_builds)
    reporter.output(debrief)

if __name__ == "__main__":
    main()
