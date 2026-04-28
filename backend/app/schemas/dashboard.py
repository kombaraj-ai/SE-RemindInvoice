"""
Pydantic schemas for Dashboard response payloads.
"""

from decimal import Decimal

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Aggregate financial and activity statistics for the dashboard header."""

    total_billed: Decimal
    total_paid: Decimal
    outstanding: Decimal
    overdue_count: int
    total_clients: int


class RevenueDataPoint(BaseModel):
    """A single month's collected revenue used to populate the revenue chart."""

    month: str  # ISO-style "YYYY-MM" e.g. "2026-01"
    revenue: Decimal


class DashboardOverview(BaseModel):
    """Combined payload returned by the overview endpoint (not currently used)."""

    stats: DashboardStats
    revenue_chart: list[RevenueDataPoint]
