"""MES connector factory."""
from connectors.sqlite_connector import SQLiteMESConnector
from connectors.api_connector import APIMESConnector
from connectors.csv_connector import CSVMESConnector


def get_connector(config: dict):
    """Get MES connector based on configuration.

    Args:
        config: Dictionary with 'mes_type' key

    Returns:
        MES connector instance

    Raises:
        ValueError: If mes_type is not supported
    """
    mes_type = config.get("mes_type")

    if mes_type == "sqlite":
        return SQLiteMESConnector(config)
    elif mes_type == "api":
        return APIMESConnector(config)
    elif mes_type == "csv":
        return CSVMESConnector(config)
    else:
        raise ValueError(f"Unsupported mes_type: {mes_type}")
