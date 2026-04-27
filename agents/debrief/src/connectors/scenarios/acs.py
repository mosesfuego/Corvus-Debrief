"""
Scenario: ACS / AeroCore Circuitry
SMT-heavy aerospace demo data with recurring feeder, QA, and staffing risk.
"""
from connectors.base import BaseMESConnector


class ACSScenarioConnector(BaseMESConnector):

    def fetch_builds(self) -> list[dict]:
        return [
            {
                "build_id": "ACS-2241",
                "station_id": "SMT_SIPLACE_B",
                "operator_id": "OP_119",
                "start_time": "2026-03-24T04:22:00",
                "planned_end": "2026-03-24T06:30:00",
                "needed_by_date": "2026-03-24T06:00:00",
                "target_quantity": 120,
                "completed_quantity": 0,
                "labor_hours": 1.8,
                "status": "Blocked",
                "notes": (
                    "ERR_FEED_MISMATCH at feeder position 22 on R0603-10K; "
                    "operator certification expired for Aero Medical build"
                ),
                "extended": {
                    "Customer_Tier": "Tier 1 Aerospace",
                    "Line_ID": "Line 3",
                    "Part_Number": "R0603-10K",
                    "Error_Code": "ERR_FEED_MISMATCH",
                    "Yield_Rate": "0.00",
                },
            },
            {
                "build_id": "ACS-2198",
                "station_id": "KITTING",
                "operator_id": "OP_088",
                "start_time": "2026-03-24T05:30:00",
                "planned_end": "2026-03-24T07:00:00",
                "needed_by_date": "2026-03-24T06:30:00",
                "target_quantity": 80,
                "completed_quantity": 0,
                "labor_hours": 1.2,
                "status": "Blocked",
                "notes": "Broker buy hold for C0402-100V substitution pending QA approval",
                "extended": {
                    "Customer_Tier": "Tier 1 Aerospace",
                    "Line_ID": "Line 5",
                    "Part_Number": "C0402-100V",
                    "Error_Code": "ERR_MAT_SHORTAGE",
                    "Yield_Rate": "0.00",
                },
            },
            {
                "build_id": "ACS-8812",
                "station_id": "AOI_01",
                "operator_id": "OP_332",
                "start_time": "2026-03-24T05:10:00",
                "planned_end": "2026-03-24T08:15:00",
                "needed_by_date": "2026-03-24T08:00:00",
                "target_quantity": 160,
                "completed_quantity": 48,
                "labor_hours": 2.4,
                "status": "In Progress",
                "notes": "FTY_LOW warning; solder bridge pattern routed to manual rework",
                "extended": {
                    "Customer_Tier": "Tier 1 Aerospace",
                    "Line_ID": "Line 4",
                    "Part_Number": "AOI-FAILURES",
                    "Error_Code": "FTY_LOW",
                    "Yield_Rate": "0.82",
                },
            },
            {
                "build_id": "ACS-5502",
                "station_id": "SMT_SIPLACE_A",
                "operator_id": "OP_221",
                "start_time": "2026-03-24T04:45:00",
                "planned_end": "2026-03-24T08:30:00",
                "needed_by_date": "2026-03-24T10:00:00",
                "target_quantity": 60,
                "completed_quantity": 52,
                "labor_hours": 2.8,
                "status": "In Progress",
                "notes": "Quick-turn prototype resumed after changeover; currently stable",
                "extended": {
                    "Customer_Tier": "Tier 3 Quick-Turn",
                    "Line_ID": "Line 2",
                    "Part_Number": "R0402-1K",
                    "Error_Code": "None",
                    "Yield_Rate": "0.98",
                },
            },
            {
                "build_id": "ACS-7740",
                "station_id": "SMT_SIPLACE_A",
                "operator_id": "OP-NOTASSIGNED",
                "start_time": "2026-03-24T07:45:00",
                "planned_end": "2026-03-24T09:30:00",
                "needed_by_date": "2026-03-24T09:15:00",
                "target_quantity": 45,
                "completed_quantity": 0,
                "labor_hours": 0.0,
                "status": "Pending",
                "notes": "Quick-turn prototype kit is ready, but no operator is assigned",
                "extended": {
                    "Customer_Tier": "Tier 3 Quick-Turn",
                    "Line_ID": "Line 6",
                    "Part_Number": "U-BQ247",
                    "Error_Code": "OPERATOR_GAP",
                    "Yield_Rate": "",
                },
            },
            {
                "build_id": "ACS-9921",
                "station_id": "CONFORMAL_COAT",
                "operator_id": "OP_551",
                "start_time": "2026-03-24T04:05:00",
                "planned_end": "2026-03-24T07:30:00",
                "needed_by_date": "2026-03-24T09:00:00",
                "target_quantity": 100,
                "completed_quantity": 76,
                "labor_hours": 3.1,
                "status": "In Progress",
                "notes": "WIP limit hit after oven temperature drift; queue is recovering",
                "extended": {
                    "Customer_Tier": "Tier 1 Aerospace",
                    "Line_ID": "Line 1",
                    "Part_Number": "C0402-GRM",
                    "Error_Code": "WIP_LIMIT_HIT",
                    "Yield_Rate": "0.99",
                },
            },
        ]

    def get_bottleneck_report(self) -> list[dict]:
        return [
            b for b in self.fetch_builds()
            if b["status"] == "Blocked"
        ]

    def get_at_risk_report(self) -> list[dict]:
        at_risk = []
        for build in self.fetch_builds():
            if (
                build["planned_end"] > build["needed_by_date"]
                and build["status"] != "Completed"
            ):
                at_risk.append(build)
        return at_risk

    def get_efficiency_by_station(self) -> dict:
        return {}
