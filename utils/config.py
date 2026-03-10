import yaml
import os
import re

def load_config(path: str = "config/config.yaml") -> dict:
    """Load YAML config, resolving ${ENV_VAR} references."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = f.read()

    # replace ${VAR_NAME} with actual env var values
    def replace_env(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            raise EnvironmentError(f"Missing environment variable: {var_name}")
        return value

    resolved = re.sub(r'\$\{(\w+)\}', replace_env, raw)
    return yaml.safe_load(resolved)
def load_onboarding(path: str = "config/onboarding.yaml") -> dict:
    """Load onboarding config."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Onboarding file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)
