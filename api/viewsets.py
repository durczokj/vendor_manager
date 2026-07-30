"""Viewsets exposed under /api/v1/.

All viewset implementations live in ``<app>/api.py``.  This module
re-exports ``CompanyViewSet`` for backward compatibility.
"""

from companies.api import CompanyViewSet

__all__ = ["CompanyViewSet"]
