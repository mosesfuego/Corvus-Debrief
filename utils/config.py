import yaml
import os

def load_config(path: str = "config/config.yaml") -> dict:
    """Load YAML config from path."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    
    return config
