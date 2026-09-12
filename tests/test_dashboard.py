import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


class TestDashboard:
    """Test dashboard and analytics endpoints."""

    def test_get_submissions_requires_auth(self, client: TestClient):
        """Test that dashboard submissions require authentication."""
        response = client.get("/dashboard/submissions")
        assert response.status_code == 403

    def test_get_submissions_success(self, client: TestClient, auth_headers, test_widget, db):
        """Test successful submission retrieval."""
        from models.submission import Submission
        
        # Create test submissions
        submission1 = Submission(
            widget_id=test_widget.id,
            tenant_id=test_widget.owner_id,
            submitted_data={"name": "Test 1", "email": "test1@example.com"},
            ip_address="192.168.1.1",
            country="United States",
            city="New York"
        )
        
        submission2 = Submission(
            widget_id=test_widget.id,
            tenant_id=test_widget.owner_id,
            submitted_data={"name": "Test 2", "email": "test2@example.com"},
            ip_address="192.168.1.2",
            country="Canada", 
            city="Toronto"
        )
        
        db.add_all([submission1, submission2])
        db.commit()
        
        response = client.get("/dashboard/submissions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        
        # Check submission structure
        submission = data[0]
        assert "id" in submission
        assert "widget_id" in submission
        assert "submitted_data" in submission
        assert "country" in submission
        assert "city" in submission
        assert "created_at" in submission

    def test_get_submissions_widget_filter(self, client: TestClient, auth_headers, test_widget, db):
        """Test filtering submissions by widget ID."""
        from models.submission import Submission
        
        # Create submission for the test widget
        submission = Submission(
            widget_id=test_widget.id,
            tenant_id=test_widget.owner_id,
            submitted_data={"name": "Filtered Test"},
            ip_address="192.168.1.1"
        )
        
        db.add(submission)
        db.commit()
        
        response = client.get(
            f"/dashboard/submissions?widget_id={test_widget.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All submissions should be for the specified widget
        for sub in data:
            assert sub["widget_id"] == test_widget.id

    def test_get_submissions_pagination(self, client: TestClient, auth_headers):
        """Test submission pagination."""
        # Test limit parameter
        response = client.get("/dashboard/submissions?limit=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
        
        # Test offset parameter
        response = client.get("/dashboard/submissions?offset=10", headers=auth_headers)
        assert response.status_code == 200

    def test_get_dashboard_stats(self, client: TestClient, auth_headers, test_widget, db):
        """Test dashboard statistics endpoint."""
        from models.submission import Submission
        
        # Create test submissions with different dates and countries
        base_date = datetime.utcnow() - timedelta(days=5)
        
        submissions = [
            Submission(
                widget_id=test_widget.id,
                tenant_id=test_widget.owner_id,
                submitted_data={"name": f"Test {i}"},
                ip_address=f"192.168.1.{i}",
                country="United States" if i % 2 == 0 else "Canada",
                city="New York" if i % 2 == 0 else "Toronto",
                created_at=base_date + timedelta(days=i % 3)
            )
            for i in range(1, 6)
        ]
        
        db.add_all(submissions)
        db.commit()
        
        response = client.get("/dashboard/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "total_submissions" in data
        assert "daily_counts" in data
        assert "geo_breakdown" in data
        assert "widget_stats" in data
        
        assert isinstance(data["daily_counts"], list)
        assert isinstance(data["geo_breakdown"], list)
        assert isinstance(data["widget_stats"], list)
        
        # Check that we have some data
        assert data["total_submissions"] >= 5

    def test_get_widget_stats_success(self, client: TestClient, auth_headers, test_widget, db):
        """Test widget-specific statistics."""
        from models.submission import Submission
        
        # Create submissions for the widget
        submissions = [
            Submission(
                widget_id=test_widget.id,
                tenant_id=test_widget.owner_id,
                submitted_data={"name": f"Widget Test {i}"},
                ip_address=f"192.168.1.{i}",
                country="Germany" if i % 2 == 0 else "France"
            )
            for i in range(1, 4)
        ]
        
        db.add_all(submissions)
        db.commit()
        
        response = client.get(f"/dashboard/widgets/{test_widget.id}/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "daily_counts" in data
        assert "geo_breakdown" in data
        assert isinstance(data["daily_counts"], list)
        assert isinstance(data["geo_breakdown"], list)

    def test_get_widget_stats_not_found(self, client: TestClient, auth_headers):
        """Test widget stats for nonexistent widget."""
        response = client.get("/dashboard/widgets/nonexistent/stats", headers=auth_headers)
        assert response.status_code == 404

    def test_dashboard_stats_tenant_isolation(self, client: TestClient, auth_headers, auth_headers_b, test_widget, test_widget_b, db):
        """Test that dashboard stats are isolated by tenant."""
        from models.submission import Submission
        
        # Create submissions for both tenants
        submission_a = Submission(
            widget_id=test_widget.id,
            tenant_id=test_widget.owner_id,
            submitted_data={"name": "Tenant A"},
            country="United States"
        )
        
        submission_b = Submission(
            widget_id=test_widget_b.id,
            tenant_id=test_widget_b.owner_id,
            submitted_data={"name": "Tenant B"},
            country="Canada"
        )
        
        db.add_all([submission_a, submission_b])
        db.commit()
        
        # Get stats for User A
        response_a = client.get("/dashboard/stats", headers=auth_headers)
        assert response_a.status_code == 200
        data_a = response_a.json()
        
        # Get stats for User B
        response_b = client.get("/dashboard/stats", headers=auth_headers_b)
        assert response_b.status_code == 200
        data_b = response_b.json()
        
        # User A should not see User B's countries in geo breakdown
        geo_countries_a = [geo["country"] for geo in data_a["geo_breakdown"]]
        if geo_countries_a:
            assert "Canada" not in geo_countries_a
        
        # User B should not see User A's countries
        geo_countries_b = [geo["country"] for geo in data_b["geo_breakdown"]]
        if geo_countries_b:
            assert "United States" not in geo_countries_b