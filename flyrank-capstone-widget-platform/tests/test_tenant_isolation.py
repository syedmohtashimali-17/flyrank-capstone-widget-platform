import pytest
from fastapi.testclient import TestClient


class TestTenantIsolation:
    """Test strict multi-tenant isolation."""

    def test_user_cannot_list_other_widgets(self, client: TestClient, auth_headers, auth_headers_b, test_widget, test_widget_b):
        """Test that User A cannot see User B's widgets in list."""
        # User A should only see their own widgets
        response = client.get("/widgets", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check User A can see their widget but not User B's
        widget_ids = [w["id"] for w in data]
        assert test_widget.id in widget_ids
        assert test_widget_b.id not in widget_ids

    def test_user_cannot_access_other_widget(self, client: TestClient, auth_headers, test_widget_b):
        """Test that User A cannot access User B's widget directly."""
        response = client.get(f"/widgets/{test_widget_b.id}", headers=auth_headers)
        assert response.status_code == 404  # Should return 404 to avoid information leakage

    def test_user_cannot_update_other_widget(self, client: TestClient, auth_headers, test_widget_b):
        """Test that User A cannot update User B's widget."""
        update_data = {"title": "Hacked Title"}
        response = client.put(f"/widgets/{test_widget_b.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 404

    def test_user_cannot_delete_other_widget(self, client: TestClient, auth_headers, test_widget_b):
        """Test that User A cannot delete User B's widget."""
        response = client.delete(f"/widgets/{test_widget_b.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_user_cannot_get_other_embed_snippet(self, client: TestClient, auth_headers, test_widget_b):
        """Test that User A cannot get User B's embed snippet."""
        response = client.get(f"/widgets/{test_widget_b.id}/embed", headers=auth_headers)
        assert response.status_code == 404

    def test_user_cannot_access_other_submissions(self, client: TestClient, auth_headers, auth_headers_b, test_widget, test_widget_b, db):
        """Test that User A cannot access User B's submissions."""
        # Create submissions for both widgets
        from models.submission import Submission
        
        # Submission for User A's widget
        submission_a = Submission(
            widget_id=test_widget.id,
            tenant_id=test_widget.owner_id,
            submitted_data={"name": "Test A", "email": "test-a@example.com"},
            ip_address="192.168.1.1"
        )
        
        # Submission for User B's widget  
        submission_b = Submission(
            widget_id=test_widget_b.id,
            tenant_id=test_widget_b.owner_id,
            submitted_data={"message": "Test message B"},
            ip_address="192.168.1.2"
        )
        
        db.add_all([submission_a, submission_b])
        db.commit()
        
        # User A should only see their submissions
        response = client.get("/dashboard/submissions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        submission_ids = [s["id"] for s in data]
        assert submission_a.id in submission_ids
        assert submission_b.id not in submission_ids
        
        # User B should only see their submissions
        response = client.get("/dashboard/submissions", headers=auth_headers_b)
        assert response.status_code == 200
        data = response.json()
        
        submission_ids = [s["id"] for s in data]
        assert submission_b.id in submission_ids
        assert submission_a.id not in submission_ids

    def test_widget_filtering_isolates_tenants(self, client: TestClient, auth_headers, test_widget_b):
        """Test that widget filtering respects tenant boundaries."""
        # User A tries to filter by User B's widget
        response = client.get(f"/dashboard/submissions?widget_id={test_widget_b.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should return empty list, not an error (no information leakage)
        assert len(data) == 0

    def test_analytics_isolate_tenants(self, client: TestClient, auth_headers, auth_headers_b, test_widget, test_widget_b, db):
        """Test that analytics only show tenant's own data."""
        from models.submission import Submission
        
        # Create submissions for both tenants
        submission_a = Submission(
            widget_id=test_widget.id,
            tenant_id=test_widget.owner_id,
            submitted_data={"name": "Test A"},
            ip_address="192.168.1.1",
            country="United States"
        )
        
        submission_b = Submission(
            widget_id=test_widget_b.id,
            tenant_id=test_widget_b.owner_id,
            submitted_data={"message": "Test B"},
            ip_address="192.168.1.2", 
            country="Canada"
        )
        
        db.add_all([submission_a, submission_b])
        db.commit()
        
        # User A's analytics should not include User B's data
        response = client.get("/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check that geo breakdown only includes User A's countries
        geo_countries = [geo["country"] for geo in data["geo_breakdown"]]
        assert "United States" in geo_countries
        assert "Canada" not in geo_countries
        
        # Check widget stats only include User A's widgets
        widget_ids = [ws["widget_id"] for ws in data["widget_stats"]]
        assert test_widget.id in widget_ids
        assert test_widget_b.id not in widget_ids

    def test_widget_stats_isolation(self, client: TestClient, auth_headers, test_widget_b):
        """Test that User A cannot access User B's widget stats."""
        response = client.get(f"/dashboard/widgets/{test_widget_b.id}/stats", headers=auth_headers)
        assert response.status_code == 404