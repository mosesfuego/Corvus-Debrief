from datetime import datetime


class BuildMetrics:

    def __init__(self, config: dict, onboarding: dict = None):
        onboarding = onboarding or {}
        thresholds = onboarding.get("thresholds", {})
        self.delay_threshold = thresholds.get("delay_minutes", 0)
        self.stall_threshold = thresholds.get("stall_minutes", 0)
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

            # completion %
            target = build.get("target_quantity", 0)
            completed = build.get("completed_quantity", 0)
            enriched["completion_pct"] = round(
                (completed / target * 100), 1
            ) if target > 0 else 0.0

            # --- deterministic signals ---
            enriched["signals"] = self._compute_signals(build, planned_end, needed_by)

            evaluated.append(enriched)
        return evaluated

    def _compute_signals(
        self,
        build: dict,
        planned_end,
        needed_by
    ) -> dict:
        """
        All signals are deterministic and reproducible.
        The agent receives facts, not raw data to interpret.
        """
        status = build.get("status", "")
        operator = build.get("operator_id", "")
        completed = build.get("completed_quantity", 0)
        labor = build.get("labor_hours", 0.0)
        target = build.get("target_quantity", 0)

        # blocked — completely stopped
        blocked = status in ("Blocked", "Stopped")

        # delayed — planned end exceeds needed by date
        delayed = bool(
            planned_end and needed_by and planned_end > needed_by
            and status != "Completed"
        )

        # stalled — labor logged but zero output
        stalled = (
            labor > (self.stall_threshold / 60)
            and completed == 0
            and status not in ("Pending", "Completed")
        )

        # at risk — behind on completion with time running out
        at_risk = delayed or (
            status == "In Progress"
            and target > 0
            and (completed / target) < 0.5
        )

        # unassigned — no operator
        unassigned = operator in ("", "UNKNOWN", "OP-NOTASSIGNED")

        # needs decision — requires human intervention
        needs_decision = blocked or (unassigned and status != "Completed")

        # paused — explicitly paused
        paused = status == "Paused"

        return {
            "blocked":        blocked,
            "delayed":        delayed,
            "stalled":        stalled,
            "at_risk":        at_risk,
            "unassigned":     unassigned,
            "needs_decision": needs_decision,
            "paused":         paused,
        }

    def _parse_dt(self, dt_string: str):
        if not dt_string:
            return None
        try:
            return datetime.fromisoformat(dt_string)
        except ValueError:
            return None
