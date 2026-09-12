import pytest
from fastapi.testclient import TestClient
from services.spam_service import SpamService


class TestHoneypot:
    """Test honeypot spam detection."""

    def test_spam_service_empty_honeypot(self):
        """Test that empty honeypot is not considered spam."""
        assert SpamService.check_honeypot("") == False
        assert SpamService.check_honeypot(None) == False

    def test_spam_service_filled_honeypot(self):
        """Test that filled honeypot is considered spam."""
        assert SpamService.check_honeypot("bot filled this") == True
        assert SpamService.check_honeypot("spam") == True
        assert SpamService.check_honeypot("   filled   ") == True

    def test_spam_service_comprehensive_check(self):
        """Test comprehensive spam detection."""
        # Valid submission
        assert SpamService.is_spam_submission(
            {"name": "John", "email": "john@example.com"}, 
            ""
        ) == False
        
        # Spam via honeypot
        assert SpamService.is_spam_submission(
            {"name": "John", "email": "john@example.com"}, 
            "bot-filled"
        ) == True

    def test_honeypot_submission_not_stored(self, client: TestClient, test_widget, db):
        """Test that honeypot submissions are not stored in database."""
        from models.submission import Submission
        
        # Count initial submissions
        initial_count = db.query(Submission).count()
        
        # Submit with filled honeypot
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Spam Bot",
                "email": "spam@bot.com"
            },
            "hp_field": "I am a bot"  # This should trigger spam detection
        }
        
        response = client.post("/submissions", json=submission_data)
        
        # Should return success (to not reveal spam detection to bots)
        assert response.status_code == 200
        
        # But no submission should be created in database
        final_count = db.query(Submission).count()
        assert final_count == initial_count  # No increase

    def test_legitimate_submission_stored(self, client: TestClient, test_widget, db):
        """Test that legitimate submissions are stored."""
        from models.submission import Submission
        
        # Count initial submissions
        initial_count = db.query(Submission).count()
        
        # Submit with empty honeypot (legitimate)
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Real Person",
                "email": "real@person.com"
            },
            "hp_field": ""  # Empty honeypot
        }
        
        response = client.post("/submissions", json=submission_data)
        
        # Should return success
        assert response.status_code == 200
        
        # Submission should be created in database
        final_count = db.query(Submission).count()
        assert final_count == initial_count + 1

    def test_honeypot_whitespace_trimming(self):
        """Test that honeypot trims whitespace properly."""
        # Whitespace-only should not be spam
        assert SpamService.check_honeypot("   ") == False
        assert SpamService.check_honeypot("\t\n") == False
        
        # Content with whitespace should be spam
        assert SpamService.check_honeypot("  spam  ") == True

    def test_multiple_honeypot_submissions(self, client: TestClient, test_widget, db):
        """Test multiple spam submissions don't create database records."""
        from models.submission import Submission
        
        initial_count = db.query(Submission).count()
        
        # Submit multiple spam requests
        for i in range(5):
            submission_data = {
                "widget_id": test_widget.id,
                "data": {
                    "name": f"Bot {i}",
                    "email": f"bot{i}@spam.com"
                },
                "hp_field": f"automated content {i}"
            }
            
            response = client.post("/submissions", json=submission_data)
            assert response.status_code == 200
        
        # No submissions should be created
        final_count = db.query(Submission).count()
        assert final_count == initial_count

    def test_honeypot_mixed_with_legitimate(self, client: TestClient, test_widget, db):
        """Test mix of spam and legitimate submissions."""
        from models.submission import Submission
        
        initial_count = db.query(Submission).count()
        
        # Legitimate submission
        legit_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Real User",
                "email": "real@example.com"
            },
            "hp_field": ""
        }
        
        # Spam submission
        spam_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Spam Bot",
                "email": "spam@bot.com"
            },
            "hp_field": "automated"
        }
        
        # Submit both
        response1 = client.post("/submissions", json=legit_data)
        response2 = client.post("/submissions", json=spam_data)
        
        # Both should return success
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Only legitimate submission should be stored
        final_count = db.query(Submission).count()
        assert final_count == initial_count + 1
        
        # Verify the stored submission is the legitimate one
        submission = db.query(Submission).filter(
            Submission.widget_id == test_widget.id
        ).order_by(Submission.id.desc()).first()
        
        assert submission.submitted_data["name"] == "Real User"