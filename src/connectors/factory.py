"""MES connector factory."""
from connectors.sqlite_connector import SQLiteMESConnector
from connectors.api_connector import APIMESConnector
from connectors.csv_connector import CSVMESConnector
from connectors.scenarios import SCENARIOS


def get_connector(config: dict):
    # scenario flag takes priority over mes_type
    scenario = config.get("scenario")
    if scenario:
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")
        return SCENARIOS[scenario](config)

    mes_type = config.get("mes_type")
    if mes_type == "sqlite":
        return SQLiteMESConnector(config)
    elif mes_type == "api":
        return APIMESConnector(config)
    elif mes_type == "csv":
        return CSVMESConnector(config)
    else:
        raise ValueError(f"Unsupported mes_type: {mes_type}")
