from datetime import datetime

class BuildMetrics:
    def __init__(self, config):
        self.delay_threshold = config.get(
            "analytics", {}
        ).get("delay_threshold_minutes", 0)

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

            # delay flag
            if planned_end and needed_by:
                enriched["delay_flag"] = planned_end > needed_by
            else:
                enriched["delay_flag"] = False

            # completion %
            target = build.get("target_quantity", 0)
            completed = build.get("completed_quantity", 0)
            enriched["completion_pct"] = round(
                (completed / target * 100), 1
            ) if target > 0 else 0.0

            evaluated.append(enriched)

        return evaluated

    def _parse_dt(self, dt_string: str):
        if not dt_string:
            return None
        try:
            return datetime.fromisoformat(dt_string)
        except ValueError:
            return None
