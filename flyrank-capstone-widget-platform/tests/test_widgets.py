import pytest
from fastapi.testclient import TestClient


class TestWidgetCRUD:
    """Test widget CRUD operations."""

    def test_create_widget_success(self, client: TestClient, auth_headers):
        """Test successful widget creation."""
        widget_data = {
            "type": "signup",
            "title": "Newsletter Signup",
            "description": "Subscribe to our newsletter",
            "form_fields": [
                {
                    "name": "name",
                    "label": "Full Name",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "email",
                    "label": "Email",
                    "type": "email",
                    "required": True
                }
            ],
            "button_text": "Subscribe"
        }
        
        response = client.post("/widgets", json=widget_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "signup"
        assert data["title"] == "Newsletter Signup"
        assert len(data["form_fields"]) == 2
        assert data["is_active"] == True
        assert "id" in data

    def test_create_widget_invalid_type(self, client: TestClient, auth_headers):
        """Test widget creation with invalid type."""
        widget_data = {
            "type": "invalid_type",
            "title": "Test Widget",
            "form_fields": [{"name": "test", "label": "Test", "type": "text", "required": False}]
        }
        
        response = client.post("/widgets", json=widget_data, headers=auth_headers)
        assert response.status_code == 422

    def test_create_widget_no_auth(self, client: TestClient):
        """Test widget creation without authentication."""
        widget_data = {
            "type": "signup",
            "title": "Test Widget",
            "form_fields": [{"name": "test", "label": "Test", "type": "text", "required": False}]
        }
        
        response = client.post("/widgets", json=widget_data)
        assert response.status_code == 403

    def test_list_widgets(self, client: TestClient, auth_headers, test_widget):
        """Test listing user's widgets."""
        response = client.get("/widgets", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(w["id"] == test_widget.id for w in data)

    def test_get_widget_success(self, client: TestClient, auth_headers, test_widget):
        """Test getting specific widget."""
        response = client.get(f"/widgets/{test_widget.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_widget.id
        assert data["title"] == test_widget.title

    def test_get_widget_not_found(self, client: TestClient, auth_headers):
        """Test getting nonexistent widget."""
        response = client.get("/widgets/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404

    def test_update_widget_success(self, client: TestClient, auth_headers, test_widget):
        """Test successful widget update."""
        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        
        response = client.put(f"/widgets/{test_widget.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"

    def test_delete_widget_success(self, client: TestClient, auth_headers, test_widget):
        """Test successful widget deletion."""
        response = client.delete(f"/widgets/{test_widget.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify widget is deleted
        response = client.get(f"/widgets/{test_widget.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_get_embed_snippet(self, client: TestClient, auth_headers, test_widget):
        """Test getting embed snippet."""
        response = client.get(f"/widgets/{test_widget.id}/embed", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["widget_id"] == test_widget.id
        assert "script" in data["snippet"]
        assert f"id={test_widget.id}" in data["snippet"]