from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class SpamService:
    """Honeypot and spam detection service."""
    
    @staticmethod
    def check_honeypot(hp_field: str) -> bool:
        """Check if the honeypot field indicates spam.
        
        Returns True if spam detected, False if legitimate.
        """
        # If honeypot field is filled, it's likely spam
        if hp_field and hp_field.strip():
            logger.info(f"Honeypot spam detected: field value length {len(hp_field)}")
            return True
        
        return False
    
    @staticmethod
    def is_spam_submission(data: Dict[str, Any], hp_field: str) -> bool:
        """Comprehensive spam check.
        
        Returns True if spam detected.
        """
        # Check honeypot
        if SpamService.check_honeypot(hp_field):
            return True
        
        # Additional spam checks could be added here:
        # - Suspicious patterns in text
        # - Too many URLs
        # - Excessive special characters
        # - Known spam phrases
        
        return False