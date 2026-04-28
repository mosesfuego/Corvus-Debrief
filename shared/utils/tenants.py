import os
import re


TENANT_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}$")


def _project_root() -> str:
    """Repository root (parent of shared/)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def tenants_root() -> str:
    return os.path.join(_project_root(), "shared", "tenants")


def validate_tenant_slug(slug: str) -> str:
    normalized = (slug or "").strip().lower()
    if not TENANT_SLUG_PATTERN.match(normalized):
        raise ValueError(
            "Tenant slug must be 2-63 chars using lowercase letters, "
            "numbers, hyphens, or underscores."
        )
    return normalized


def get_tenant_context(slug: str) -> dict:
    """
    Local stand-in for the future SaaS tenant context.
    Every tenant-scoped path is derived from this one validated slug.
    """
    slug = validate_tenant_slug(slug)
    root = os.path.join(tenants_root(), slug)
    return {
        "slug": slug,
        "root": root,
        "onboarding_path": os.path.join(root, "onboarding.yaml"),
        "reports_dir": os.path.join(root, "reports"),
        "memory_path": os.path.join(root, "memory", "log.json"),
        "uploads_dir": os.path.join(root, "uploads"),
    }


def list_tenants() -> list[str]:
    root = tenants_root()
    if not os.path.isdir(root):
        return []

    tenants = []
    for name in os.listdir(root):
        try:
            context = get_tenant_context(name)
        except ValueError:
            continue
        if os.path.isfile(context["onboarding_path"]):
            tenants.append(context["slug"])
    return sorted(tenants)
