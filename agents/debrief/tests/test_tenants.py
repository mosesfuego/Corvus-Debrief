import os
import sys

import pytest

_THIS_FILE = os.path.abspath(__file__)
_TESTS_DIR = os.path.dirname(_THIS_FILE)
_AGENT_ROOT = os.path.dirname(_TESTS_DIR)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))
_SHARED_DIR = os.path.join(_PROJECT_ROOT, "shared")

sys.path.insert(0, _SHARED_DIR)

from utils.tenants import get_tenant_context, validate_tenant_slug


def test_validate_tenant_slug_normalizes_safe_values():
    assert validate_tenant_slug(" AeroCore_01 ") == "aerocore_01"


@pytest.mark.parametrize("slug", ["", "a", "../acme", "Acme!", "acme plant"])
def test_validate_tenant_slug_rejects_unsafe_values(slug):
    with pytest.raises(ValueError):
        validate_tenant_slug(slug)


def test_get_tenant_context_scopes_paths_under_tenant_root():
    context = get_tenant_context("aerocore")

    assert context["slug"] == "aerocore"
    assert context["onboarding_path"].endswith(
        os.path.join("shared", "tenants", "aerocore", "onboarding.yaml")
    )
    assert context["reports_dir"].endswith(
        os.path.join("shared", "tenants", "aerocore", "reports")
    )
    assert context["memory_path"].endswith(
        os.path.join("shared", "tenants", "aerocore", "memory", "log.json")
    )
