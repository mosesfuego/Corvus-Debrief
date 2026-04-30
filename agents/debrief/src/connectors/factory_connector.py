"""Compatibility wrapper for older imports.

New code should import from connectors.factory.
"""

from connectors.factory import clear_connector_cache, get_connector

__all__ = ["clear_connector_cache", "get_connector"]
