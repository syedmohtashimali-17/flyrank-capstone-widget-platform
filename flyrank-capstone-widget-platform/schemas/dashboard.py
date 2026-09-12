from datetime import date
from typing import List
from pydantic import BaseModel


class DailyCount(BaseModel):
    date: date
    count: int


class GeoBreakdown(BaseModel):
    country: str
    count: int


class WidgetStats(BaseModel):
    widget_id: str
    title: str
    total_submissions: int


class DashboardStats(BaseModel):
    total_submissions: int
    daily_counts: List[DailyCount]
    geo_breakdown: List[GeoBreakdown]
    widget_stats: List[WidgetStats]


class SubmissionStats(BaseModel):
    daily_counts: List[DailyCount]
    geo_breakdown: List[GeoBreakdown]