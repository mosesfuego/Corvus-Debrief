"""Tests for intake, canonical, domain, and orchestration layers."""

import os
import sys

_THIS_FILE = os.path.abspath(__file__)
_TESTS_DIR = os.path.dirname(_THIS_FILE)
_AGENT_ROOT = os.path.dirname(_TESTS_DIR)
_SRC_DIR = os.path.join(_AGENT_ROOT, "src")
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))
_SHARED_DIR = os.path.join(_PROJECT_ROOT, "shared")

sys.path.insert(0, _PROJECT_ROOT)
sys.path.insert(0, _SHARED_DIR)
sys.path.insert(0, _SRC_DIR)

from canonical.work_order import WorkOrder
from agent_runtime.context import AgentContext
from agent_runtime.registry import AgentRegistry
from domain_agents.materials_lite_agent import MaterialsLiteAgent
from domain_agents.quality_lite_agent import QualityLiteAgent
from domain_agents.labor.agent import LaborAgent
from domain_agents.schedule.agent import ScheduleAgent
from domain_agents.work_order.agent import WorkOrderAgent
from intake.source_classifier import classify_headers
from intake.schema_mapper import propose_mapping_with_heuristics
from orchestration.debrief_orchestrator import DebriefOrchestrator
from workflows.debrief.orchestrator import DebriefOrchestrator as WorkflowOrchestrator


def test_source_classifier_identifies_work_order_headers():
    result = classify_headers([
        "Job_ID",
        "Work_Center",
        "Status",
        "Target_Qty",
        "Completed_Qty",
    ])

    assert result["source_type"] == "work_order"
    assert result["confidence"] > 0


def test_schema_mapper_uses_registry_aliases():
    proposal = propose_mapping_with_heuristics([
        "WO_ID",
        "Machine",
        "Current_Status",
    ])

    mapping = proposal["mapping"]
    assert mapping["build_id"]["csv_column"] == "WO_ID"
    assert mapping["station_id"]["csv_column"] == "Machine"
    assert mapping["status"]["csv_column"] == "Current_Status"


def test_work_order_canonical_normalizes_types():
    work_order = WorkOrder.from_raw({
        "build_id": "WO-1",
        "target_quantity": "10.0",
        "completed_quantity": "4",
        "labor_hours": "2.5",
    })

    assert work_order.target_quantity == 10
    assert work_order.completed_quantity == 4
    assert work_order.labor_hours == 2.5
    assert work_order.to_dict()["status"] == "Unknown"


def test_lite_domain_agents_extract_cross_domain_findings():
    builds = [
        {
            "build_id": "WO-QA",
            "station_id": "KITTING",
            "notes": "Broker buy hold pending QA approval",
            "extended": {
                "Part_Number": "C0402-100V",
                "Error_Code": "ERR_MAT_SHORTAGE",
            },
        }
    ]

    quality = QualityLiteAgent().evaluate(builds)
    materials = MaterialsLiteAgent().evaluate(builds)

    assert quality["findings"][0]["owner"] == "Quality Assurance"
    assert materials["findings"][0]["owner"] == "Materials"


def test_domain_agents_share_standard_result_shape():
    context = AgentContext.from_builds(
        [
            {
                "build_id": "WO-LABOR",
                "station_id": "SMT",
                "operator_id": "",
                "status": "In Progress",
                "notes": "Operator certification expired",
            }
        ],
        config={},
        onboarding={"thresholds": {"stall_minutes": 20}},
    )

    work_order = WorkOrderAgent({}, {}).evaluate(context)
    context.builds = work_order["builds"]
    schedule = ScheduleAgent().evaluate(context)
    labor = LaborAgent().evaluate(context)

    for result in (work_order, schedule, labor):
        assert {"domain", "summary", "findings"}.issubset(result)
        assert isinstance(result["findings"], list)

    assert labor["summary"]["finding_count"] > 0


def test_agent_registry_uses_configured_agents_with_work_order_first():
    registry = AgentRegistry({
        "domain_agents": {"enabled": ["quality", "materials"]}
    })

    assert registry.enabled_names() == ["work_order", "quality", "materials"]


def test_debrief_orchestrator_returns_legacy_and_domain_context():
    config = {"mes_type": "scenario", "scenario": "acs"}
    onboarding = {
        "thresholds": {"stall_minutes": 20},
        "terminology": {"build": "work order", "operator": "operator"},
    }

    context = DebriefOrchestrator(config, onboarding).build_context()

    assert context["summary"]["total"] == 6
    assert context["signals"]["blocked"]
    assert context["domains"]["work_order"]["domain"] == "work_order"
    assert "builds" not in context["domains"]["work_order"]
    assert context["domains"]["quality"]["findings"]
    assert context["domains"]["materials"]["findings"]
    assert context["domains"]["schedule"]["domain"] == "schedule"
    assert context["domains"]["labor"]["domain"] == "labor"
    assert context["agent_order"] == [
        "work_order",
        "materials",
        "quality",
        "schedule",
        "labor",
    ]


def test_legacy_orchestrator_import_uses_workflow_orchestrator():
    assert DebriefOrchestrator is WorkflowOrchestrator
