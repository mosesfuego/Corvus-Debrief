"""MES connector factory."""
from connectors.csv_connector import CSVMESConnector
from connectors.sqlite_connector import SQLiteMESConnector
from connectors.api_connector import APIMESConnector
from connectors.scenarios import SCENARIOS

# module-level cache — same connector instance reused within a run
_connector_cache = {}


def get_connector(config: dict, onboarding: dict = None):
    """Get MES connector based on configuration."""

    # scenario flag takes priority
    scenario = config.get("scenario")
    if scenario:
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")
        return SCENARIOS[scenario](config)

    mes_type = config.get("mes_type")
    file_path = config.get("csv_file_path")

    # cache key — unique per mes_type + file_path combination
    cache_key = f"{mes_type}:{file_path}"

    if cache_key in _connector_cache:
        return _connector_cache[cache_key]

    if mes_type in ("csv", "flexible_csv"):
        connector = CSVMESConnector(config, onboarding or {}, file_path=file_path)
    elif mes_type == "sqlite":
        connector = SQLiteMESConnector(config)
    elif mes_type == "api":
        connector = APIMESConnector(config)
    else:
        raise ValueError(f"Unsupported mes_type: {mes_type}")

    _connector_cache[cache_key] = connector
    return connector


def clear_connector_cache():
    """Call this between runs if needed."""
    global _connector_cache
    _connector_cache = {}
