def get_connector(config):
    if config["mes_type"] == "sqlite":
        return SQLiteMESConnector(config)
    elif config["mes_type"] == "api":
        return APIMESConnector(config)
    elif config["mes_type"] == "csv":
        return CSVMESConnector(config)
    else:
        raise ValueError("Unsupported MES type")
