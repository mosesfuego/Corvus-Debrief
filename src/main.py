# src/main.py

import time
from config.loader import load_config
from connectors.mes_simulation import MESConnector
from analytics.build_metrics import BuildMetrics
from reporting.debrief_template import DebriefGenerator


def main():
    config = load_config()

    connector = MESConnector(config)
    analytics = BuildMetrics(config)
    reporter = DebriefGenerator(config)

    poll_interval = config.get("poll_interval_seconds", 60)

    while True:
        builds = connector.fetch_latest_builds()
        analyzed_builds = analytics.evaluate(builds)
        debrief = reporter.generate(analyzed_builds)
        reporter.output(debrief)

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
