def main():
    config = load_config()

    connector = MESConnector(config)
    analytics_engine = BuildMetrics(config)
    reporter = DebriefGenerator(config)

    builds = connector.fetch_latest_builds()

    analyzed_builds = analytics_engine.evaluate(builds)

    debrief = reporter.generate(analyzed_builds)

    reporter.output(debrief)


if __name__ == "__main__":
    main()
