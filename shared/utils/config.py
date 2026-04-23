import yaml
import os
import re

SUPPORTED_SCHEMA_VERSIONS = ["1.0"]


def _project_root() -> str:
    """Repository root (parent of shared/)."""
    _here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(_here))


def _resolve_repo_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    if os.path.isfile(path):
        return os.path.abspath(path)
    return os.path.normpath(os.path.join(_project_root(), path))


def load_config(path: str = "agents/debrief/config/config.yaml") -> dict:
    _load_dotenv()
    path = _resolve_repo_path(path)

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
    data = yaml.safe_load(resolved)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")
    return data


def load_onboarding(path: str = "agents/debrief/config/onboarding.yaml") -> dict:
    path = _resolve_repo_path(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Onboarding file not found: {path}")
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Onboarding file must be a YAML mapping: {path}")
    version = data.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(
            f"Unsupported onboarding schema version: '{version}'\n"
            f"Supported versions: {SUPPORTED_SCHEMA_VERSIONS}\n"
            f"Check your onboarding.yaml."
        )
    return data


def _load_dotenv():
    """Load .env from project root, then cwd (setdefault — first wins)."""
    for root in (_project_root(), os.getcwd()):
        path = os.path.join(root, ".env")
        if not os.path.isfile(path):
            continue
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
