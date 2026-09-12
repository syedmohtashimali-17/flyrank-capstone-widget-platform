from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models.submission import Submission
from models.widget import Widget
from schemas.dashboard import DailyCount, GeoBreakdown, WidgetStats, DashboardStats, SubmissionStats


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_daily_counts(
        self, 
        tenant_id: int, 
        widget_id: Optional[str] = None,
        days: int = 30
    ) -> List[DailyCount]:
        """Get daily submission counts for the last N days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.query(
            func.date(Submission.created_at).label('date'),
            func.count(Submission.id).label('count')
        ).filter(
            Submission.tenant_id == tenant_id,
            func.date(Submission.created_at) >= start_date
        )
        
        if widget_id:
            query = query.filter(Submission.widget_id == widget_id)
        
        results = query.group_by(func.date(Submission.created_at)).all()
        
        # Convert to list of DailyCount objects, filling in missing days with 0
        daily_counts = {}
        for result in results:
            daily_counts[result.date] = result.count
        
        # Fill in missing days
        counts = []
        current_date = start_date
        while current_date <= end_date:
            count = daily_counts.get(current_date, 0)
            counts.append(DailyCount(date=current_date, count=count))
            current_date += timedelta(days=1)
        
        return counts
    
    def get_geo_breakdown(
        self, 
        tenant_id: int, 
        widget_id: Optional[str] = None,
        limit: int = 10
    ) -> List[GeoBreakdown]:
        """Get geographical breakdown of submissions."""
        query = self.db.query(
            Submission.country,
            func.count(Submission.id).label('count')
        ).filter(
            Submission.tenant_id == tenant_id,
            Submission.country.isnot(None)
        )
        
        if widget_id:
            query = query.filter(Submission.widget_id == widget_id)
        
        results = query.group_by(Submission.country)\
                      .order_by(desc('count'))\
                      .limit(limit)\
                      .all()
        
        return [GeoBreakdown(country=result.country, count=result.count) for result in results]
    
    def get_widget_stats(self, tenant_id: int) -> List[WidgetStats]:
        """Get submission counts per widget for a tenant."""
        results = self.db.query(
            Widget.id,
            Widget.title,
            func.count(Submission.id).label('total_submissions')
        ).outerjoin(Submission)\
         .filter(Widget.owner_id == tenant_id)\
         .group_by(Widget.id, Widget.title)\
         .order_by(desc('total_submissions'))\
         .all()
        
        return [
            WidgetStats(
                widget_id=result.id,
                title=result.title,
                total_submissions=result.total_submissions or 0
            ) 
            for result in results
        ]
    
    def get_dashboard_stats(self, tenant_id: int) -> DashboardStats:
        """Get comprehensive dashboard statistics."""
        # Total submissions
        total_submissions = self.db.query(func.count(Submission.id))\
                                  .filter(Submission.tenant_id == tenant_id)\
                                  .scalar()
        
        # Get component stats
        daily_counts = self.get_daily_counts(tenant_id)
        geo_breakdown = self.get_geo_breakdown(tenant_id)
        widget_stats = self.get_widget_stats(tenant_id)
        
        return DashboardStats(
            total_submissions=total_submissions,
            daily_counts=daily_counts,
            geo_breakdown=geo_breakdown,
            widget_stats=widget_stats
        )
    
    def get_widget_analytics(self, tenant_id: int, widget_id: str) -> SubmissionStats:
        """Get analytics for a specific widget."""
        # Verify widget belongs to tenant
        widget = self.db.query(Widget).filter(
            Widget.id == widget_id,
            Widget.owner_id == tenant_id
        ).first()
        
        if not widget:
            from core.errors import NotFoundError
            raise NotFoundError("Widget not found")
        
        daily_counts = self.get_daily_counts(tenant_id, widget_id)
        geo_breakdown = self.get_geo_breakdown(tenant_id, widget_id)
        
        return SubmissionStats(
            daily_counts=daily_counts,
            geo_breakdown=geo_breakdown
        )