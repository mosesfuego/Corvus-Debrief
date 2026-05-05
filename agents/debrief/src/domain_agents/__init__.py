"""Domain agents that reason over canonical manufacturing records."""
"""Corvus manufacturing domain agents."""

from domain_agents.labor.agent import LaborAgent
from domain_agents.materials.agent import MaterialsAgent, MaterialsLiteAgent
from domain_agents.quality.agent import QualityAgent, QualityLiteAgent
from domain_agents.schedule.agent import ScheduleAgent
from domain_agents.work_order.agent import WorkOrderAgent

__all__ = [
    "LaborAgent",
    "MaterialsAgent",
    "MaterialsLiteAgent",
    "QualityAgent",
    "QualityLiteAgent",
    "ScheduleAgent",
    "WorkOrderAgent",
]
