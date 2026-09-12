import pytest
from fastapi.testclient import TestClient


class TestPublicConfig:
    """Test public widget configuration delivery."""

    def test_get_widget_config_success(self, client: TestClient, test_widget):
        """Test successful widget config retrieval."""
        response = client.get(f"/widgets/{test_widget.id}/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields are present
        assert data["id"] == test_widget.id
        assert data["type"] == test_widget.type
        assert data["title"] == test_widget.title
        assert data["description"] == test_widget.description
        assert data["form_fields"] == test_widget.form_fields
        assert data["button_text"] == test_widget.button_text
        assert data["version"] == test_widget.version
        
        # Check private data is not exposed
        assert "owner_id" not in data
        assert "password" not in data
        assert "password_hash" not in data
        assert "created_at" not in data
        assert "updated_at" not in data

    def test_get_widget_config_not_found(self, client: TestClient):
        """Test widget config for nonexistent widget."""
        response = client.get("/widgets/nonexistent-id/config")
        assert response.status_code == 404

    def test_get_widget_config_inactive_widget(self, client: TestClient, db, test_widget):
        """Test widget config for inactive widget."""
        # Make widget inactive
        test_widget.is_active = False
        db.commit()
        
        response = client.get(f"/widgets/{test_widget.id}/config")
        assert response.status_code == 404

    def test_widget_config_cache_headers(self, client: TestClient, test_widget):
        """Test that appropriate cache headers are set."""
        response = client.get(f"/widgets/{test_widget.id}/config")
        
        assert response.status_code == 200
        
        # Check cache headers
        assert "Cache-Control" in response.headers
        assert "public" in response.headers["Cache-Control"]
        assert "max-age=300" in response.headers["Cache-Control"]

    def test_widget_config_cors_headers(self, client: TestClient, test_widget):
        """Test that CORS headers are set for public config."""
        response = client.get(f"/widgets/{test_widget.id}/config")
        
        assert response.status_code == 200
        
        # Check CORS headers
        assert response.headers.get("Access-Control-Allow-Origin") == "*"
        assert "GET" in response.headers.get("Access-Control-Allow-Methods", "")
        assert "OPTIONS" in response.headers.get("Access-Control-Allow-Methods", "")

    def test_widget_config_no_auth_required(self, client: TestClient, test_widget):
        """Test that widget config doesn't require authentication."""
        # This should work without any authentication headers
        response = client.get(f"/widgets/{test_widget.id}/config")
        assert response.status_code == 200

    def test_widget_config_display_options(self, client: TestClient, db, test_widget):
        """Test that display options are included in config."""
        # Update widget with display options
        test_widget.display_options = {"position": "bottom-right", "theme": "blue"}
        db.commit()
        
        response = client.get(f"/widgets/{test_widget.id}/config")
        
        assert response.status_code == 200
        data = response.json()
        assert data["display_options"]["position"] == "bottom-right"
        assert data["display_options"]["theme"] == "blue"

    def test_widget_config_form_fields_structure(self, client: TestClient, test_widget):
        """Test that form fields have correct structure."""
        response = client.get(f"/widgets/{test_widget.id}/config")
        
        assert response.status_code == 200
        data = response.json()
        
        form_fields = data["form_fields"]
        assert isinstance(form_fields, list)
        assert len(form_fields) > 0
        
        for field in form_fields:
            assert "name" in field
            assert "label" in field
            assert "type" in field
            assert "required" in field