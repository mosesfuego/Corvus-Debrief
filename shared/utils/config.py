import yaml
import os
import re
SUPPORTED_SCHEMA_VERSIONS = ["1.0"]
def load_config(path: str = "agents/debrief/config/config.yaml") -> dict:
    # auto-load .env if it exists
    _load_dotenv()

    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = f.read()

    def replace_env(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            raise EnvironmentError(f"Missing environment variable: {var_name}")
        return value

    resolved = re.sub(r'\$\{(\w+)\}', replace_env, raw)
    return yaml.safe_load(resolved)


def load_onboarding(path: str = "agents/debrief/config/onboarding.yaml") -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Onboarding file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)
    version = data.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(
            f"Unsupported onboarding schema version: '{version}'\n"
            f"Supported versions: {SUPPORTED_SCHEMA_VERSIONS}\n"
            f"Check your onboarding.yaml."
        )
    return data


def _load_dotenv(path: str = ".env"):
    """Simple .env loader — no dependencies needed."""
    if not os.path.exists(path):
        return
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
