"""Serializers used by the API surface.

All serializer implementations live in ``<app>/serializers.py``.  This module
re-exports ``CompanySerializer`` for backward compatibility.
"""

from companies.serializers import CompanySerializer

__all__ = ["CompanySerializer"]
