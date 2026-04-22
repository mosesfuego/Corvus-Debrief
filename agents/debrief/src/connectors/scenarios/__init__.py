from connectors.scenarios.normal import NormalScenarioConnector
from connectors.scenarios.crisis import CrisisScenarioConnector
from connectors.scenarios.staffing import StaffingScenarioConnector

SCENARIOS = {
    "normal": NormalScenarioConnector,
    "crisis": CrisisScenarioConnector,
    "staffing": StaffingScenarioConnector,
}
