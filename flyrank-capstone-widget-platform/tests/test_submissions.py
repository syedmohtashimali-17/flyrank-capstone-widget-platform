import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestSubmissions:
    """Test submission endpoints and validation."""

    def test_cors_preflight_submissions(self, client: TestClient):
        """Test CORS preflight for submissions endpoint."""
        response = client.options("/submissions")
        
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "*"
        assert "POST" in response.headers.get("Access-Control-Allow-Methods", "")
        assert "OPTIONS" in response.headers.get("Access-Control-Allow-Methods", "")
        assert "Content-Type" in response.headers.get("Access-Control-Allow-Headers", "")

    def test_create_submission_success(self, client: TestClient, test_widget):
        """Test successful submission creation."""
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "John Doe",
                "email": "john@example.com"
            },
            "hp_field": ""  # Empty honeypot
        }
        
        response = client.post("/submissions", json=submission_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "message" in data
        
        # Check CORS headers in response
        assert response.headers.get("Access-Control-Allow-Origin") == "*"

    def test_create_submission_invalid_widget(self, client: TestClient):
        """Test submission with invalid widget ID."""
        submission_data = {
            "widget_id": "nonexistent-widget",
            "data": {
                "name": "John Doe"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 404

    def test_create_submission_missing_required_field(self, client: TestClient, test_widget):
        """Test submission missing required field."""
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "John Doe"
                # Missing required email field
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 422

    def test_create_submission_unknown_field(self, client: TestClient, test_widget):
        """Test submission with unknown field."""
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "John Doe",
                "email": "john@example.com",
                "unknown_field": "unknown value"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 422

    def test_create_submission_invalid_email(self, client: TestClient, test_widget):
        """Test submission with invalid email format."""
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "John Doe",
                "email": "invalid-email"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 422

    def test_create_submission_malformed_json(self, client: TestClient):
        """Test submission with malformed JSON."""
        response = client.post(
            "/submissions", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_submission_oversized_payload(self, client: TestClient, test_widget):
        """Test submission with oversized payload."""
        # Create a large payload
        large_data = "x" * 70000  # Larger than 64KB limit
        
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": large_data,
                "email": "test@example.com"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 413
        
        data = response.json()
        assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"

    @patch('services.submission_service.side_effect_service')
    def test_create_submission_stores_in_database(self, mock_side_effect, client: TestClient, test_widget, db):
        """Test that valid submission is stored in database."""
        from models.submission import Submission
        
        # Count initial submissions
        initial_count = db.query(Submission).count()
        
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Database Test",
                "email": "dbtest@example.com"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 200
        
        # Check submission was created in database
        final_count = db.query(Submission).count()
        assert final_count == initial_count + 1
        
        # Verify submission data
        submission = db.query(Submission).filter(
            Submission.widget_id == test_widget.id
        ).first()
        
        assert submission is not None
        assert submission.submitted_data["name"] == "Database Test"
        assert submission.submitted_data["email"] == "dbtest@example.com"
        assert submission.tenant_id == test_widget.owner_id

    def test_submission_with_idempotency_key(self, client: TestClient, test_widget):
        """Test submission with idempotency key."""
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Idempotent Test",
                "email": "idem@example.com"
            },
            "hp_field": ""
        }
        
        headers = {"Idempotency-Key": "test-key-123"}
        
        # First submission
        response = client.post("/submissions", json=submission_data, headers=headers)
        assert response.status_code == 200
        
        # Second submission with same key should not create duplicate
        response = client.post("/submissions", json=submission_data, headers=headers)
        assert response.status_code == 200

    def test_submission_inactive_widget(self, client: TestClient, db, test_widget):
        """Test submission to inactive widget fails."""
        # Make widget inactive
        test_widget.is_active = False
        db.commit()
        
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Test Name",
                "email": "test@example.com"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 404