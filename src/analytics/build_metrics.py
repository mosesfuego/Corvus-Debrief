from datetime import datetime


class BuildMetrics:

    def __init__(self, config: dict, onboarding: dict = None):
        onboarding = onboarding or {}
        thresholds = onboarding.get("thresholds", {})

        # thresholds now come from onboarding, not config
        self.delay_threshold = thresholds.get("delay_minutes", 0)
        self.stall_threshold = thresholds.get("stall_minutes", 0)

        # terminology mapping — speak the customer's language
        terminology = onboarding.get("terminology", {})
        self.term_build = terminology.get("build", "build")
        self.term_operator = terminology.get("operator", "operator")

    def evaluate(self, builds: list[dict]) -> list[dict]:
        evaluated = []

        for build in builds:
            enriched = build.copy()

            start = self._parse_dt(build.get("start_time"))
            planned_end = self._parse_dt(build.get("planned_end"))
            needed_by = self._parse_dt(build.get("needed_by_date"))

            # duration
            if start and planned_end:
                duration = (planned_end - start).total_seconds() / 3600
                enriched["duration_hours"] = round(duration, 2)
            else:
                enriched["duration_hours"] = None

            # delay flag — uses onboarding threshold
            if planned_end and needed_by:
                diff_minutes = (planned_end - needed_by).total_seconds() / 60
                enriched["delay_flag"] = diff_minutes > self.delay_threshold
            else:
                enriched["delay_flag"] = False

            # stall flag — no progress relative to stall threshold
            labor = build.get("labor_hours", 0)
            completion = build.get("completed_quantity", 0)
            enriched["stall_flag"] = (
                labor > (self.stall_threshold / 60) and completion == 0
            )

            # completion %
            target = build.get("target_quantity", 0)
            completed = build.get("completed_quantity", 0)
            enriched["completion_pct"] = round(
                (completed / target * 100), 1
            ) if target > 0 else 0.0

            # signal classification — maps to watch_signals in onboarding
            enriched["signals"] = self._classify_signals(enriched)

            evaluated.append(enriched)

        return evaluated

    def _classify_signals(self, build: dict) -> list[str]:
        """
        Classify build into signals that match watch_signals in onboarding.
        These are used by the reporter to route findings to the right team.
        """
        signals = []

        if build.get("status") == "Blocked":
            signals.append("stalled_build")

        if build.get("status") == "Paused":
            signals.append("paused_build")

        if build.get("delay_flag"):
            signals.append("delayed_build")

        if build.get("stall_flag"):
            signals.append("stalled_build")

        if build.get("operator_id") == "OP-NOTASSIGNED":
            signals.append("unassigned_operator")

        return signals

    def _parse_dt(self, dt_string: str):
        if not dt_string:
            return None
        try:
            return datetime.fromisoformat(dt_string)
        except ValueError:
            return None
