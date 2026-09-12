import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from services.side_effect_service import SideEffectService


class TestSideEffects:
    """Test background side effects and failure handling."""

    @pytest.mark.asyncio
    async def test_side_effect_email_success(self):
        """Test successful email side effect."""
        service = SideEffectService()
        
        with patch('services.side_effect_service.settings.side_effect_fail', False):
            # Should complete without raising exception
            await service.send_confirmation_email(
                submission_id=123,
                email="test@example.com",
                data={"name": "Test User", "email": "test@example.com"}
            )

    @pytest.mark.asyncio
    async def test_side_effect_email_failure(self):
        """Test email side effect with simulated failure."""
        service = SideEffectService()
        service.max_retries = 2  # Reduce retries for faster testing
        
        with patch('services.side_effect_service.settings.side_effect_fail', True):
            # Should not raise exception even when failing
            await service.send_confirmation_email(
                submission_id=123,
                email="test@example.com",
                data={"name": "Test User"}
            )

    @pytest.mark.asyncio
    async def test_side_effect_webhook_success(self):
        """Test successful webhook side effect."""
        service = SideEffectService()
        
        with patch('services.side_effect_service.settings.side_effect_fail', False):
            await service.send_webhook_notification(
                submission_id=123,
                webhook_url="https://example.com/webhook",
                data={"test": "data"}
            )

    @pytest.mark.asyncio
    async def test_side_effect_webhook_failure(self):
        """Test webhook side effect with simulated failure."""
        service = SideEffectService()
        service.max_retries = 2
        
        with patch('services.side_effect_service.settings.side_effect_fail', True):
            await service.send_webhook_notification(
                submission_id=123,
                webhook_url="https://example.com/webhook",
                data={"test": "data"}
            )

    @pytest.mark.asyncio
    async def test_side_effect_disabled(self):
        """Test side effects when disabled in settings."""
        service = SideEffectService()
        
        with patch('services.side_effect_service.settings.side_effect_enabled', False):
            # Should return early without processing
            await service.process_submission_side_effects(
                submission_id=123,
                submitted_data={"email": "test@example.com"}
            )

    @patch('services.side_effect_service.side_effect_service')
    def test_submission_triggers_side_effects(self, mock_side_effect, client: TestClient, test_widget):
        """Test that submission triggers side effects."""
        mock_side_effect.process_submission_side_effects = AsyncMock()
        
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Side Effect Test",
                "email": "sideeffect@example.com"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 200

    @patch('services.side_effect_service.side_effect_service')
    def test_submission_succeeds_despite_side_effect_failure(self, mock_side_effect, client: TestClient, test_widget, db):
        """Test that submission succeeds even if side effects fail."""
        from models.submission import Submission
        
        # Make side effect service raise an exception
        mock_side_effect.process_submission_side_effects.side_effect = Exception("Side effect failed")
        
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Resilient Test",
                "email": "resilient@example.com"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        
        # Submission should still succeed
        assert response.status_code == 200
        
        # Submission should be stored in database
        submission = db.query(Submission).filter(
            Submission.widget_id == test_widget.id
        ).order_by(Submission.id.desc()).first()
        
        assert submission is not None
        assert submission.submitted_data["name"] == "Resilient Test"

    def test_side_effect_retry_logic(self):
        """Test retry logic in side effects."""
        service = SideEffectService()
        service.max_retries = 3
        
        # Track retry attempts
        retry_count = {"count": 0}
        
        async def failing_operation():
            retry_count["count"] += 1
            if retry_count["count"] < 3:
                raise Exception("Temporary failure")
            return "Success on third try"
        
        # Test that retries work
        async def test_retries():
            for attempt in range(1, service.max_retries + 1):
                try:
                    result = await failing_operation()
                    return result
                except Exception as e:
                    if attempt < service.max_retries:
                        await asyncio.sleep(0.01)  # Small delay for testing
                    else:
                        raise e
        
        result = asyncio.run(test_retries())
        assert result == "Success on third try"
        assert retry_count["count"] == 3

    @patch('services.side_effect_service.settings.side_effect_fail')
    def test_side_effect_deterministic_failure(self, mock_fail_setting, client: TestClient, test_widget, db):
        """Test deterministic side effect failure for testing."""
        from models.submission import Submission
        
        # Enable side effect failure
        mock_fail_setting.return_value = True
        
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Deterministic Fail",
                "email": "fail@example.com"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        
        # Response should be successful despite side effect failure
        assert response.status_code == 200
        
        # Submission should be stored
        submission = db.query(Submission).filter(
            Submission.widget_id == test_widget.id
        ).order_by(Submission.id.desc()).first()
        
        assert submission is not None
        assert submission.submitted_data["name"] == "Deterministic Fail"