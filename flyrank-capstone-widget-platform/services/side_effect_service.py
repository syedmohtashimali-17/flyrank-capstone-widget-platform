import asyncio
import logging
from typing import Dict, Any
from core.config import settings

logger = logging.getLogger(__name__)


class SideEffectService:
    """Background side effect service with retry logic."""
    
    def __init__(self):
        self.max_retries = settings.side_effect_retries
    
    async def send_confirmation_email(self, submission_id: int, email: str, data: Dict[str, Any]) -> None:
        """Simulate sending a confirmation email."""
        if not settings.side_effect_enabled:
            logger.info(f"Side effects disabled - skipping email for submission {submission_id}")
            return
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Sending confirmation email for submission {submission_id} (attempt {attempt})")
                
                # Simulate email sending
                if settings.side_effect_fail:
                    raise Exception("Simulated side effect failure")
                
                # Simulate network delay
                await asyncio.sleep(0.1)
                
                logger.info(f"Confirmation email sent successfully for submission {submission_id}")
                return
                
            except Exception as e:
                logger.error(f"Confirmation email failed for submission {submission_id} (attempt {attempt}): {e}")
                
                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = 2 ** (attempt - 1)
                    logger.info(f"Retrying confirmation email in {delay} seconds")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for confirmation email, submission {submission_id}")
                    # In production, this could trigger an alert
                    break
    
    async def send_webhook_notification(self, submission_id: int, webhook_url: str, data: Dict[str, Any]) -> None:
        """Simulate sending a webhook notification."""
        if not settings.side_effect_enabled:
            logger.info(f"Side effects disabled - skipping webhook for submission {submission_id}")
            return
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Sending webhook notification for submission {submission_id} (attempt {attempt})")
                
                # Simulate webhook sending  
                if settings.side_effect_fail:
                    raise Exception("Simulated webhook failure")
                
                # Simulate network delay
                await asyncio.sleep(0.1)
                
                logger.info(f"Webhook notification sent successfully for submission {submission_id}")
                return
                
            except Exception as e:
                logger.error(f"Webhook notification failed for submission {submission_id} (attempt {attempt}): {e}")
                
                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = 2 ** (attempt - 1)  
                    logger.info(f"Retrying webhook in {delay} seconds")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for webhook notification, submission {submission_id}")
                    break
    
    async def process_submission_side_effects(self, submission_id: int, submitted_data: Dict[str, Any]) -> None:
        """Process all side effects for a submission."""
        if not settings.side_effect_enabled:
            return
        
        try:
            # Extract email if present
            email = None
            for key, value in submitted_data.items():
                if 'email' in key.lower() and '@' in str(value):
                    email = str(value)
                    break
            
            # Run side effects concurrently but don't wait for completion
            tasks = []
            
            if email:
                tasks.append(self.send_confirmation_email(submission_id, email, submitted_data))
            
            # Example webhook - in production this would be configurable per widget
            webhook_url = "https://example.com/webhook"
            tasks.append(self.send_webhook_notification(submission_id, webhook_url, submitted_data))
            
            if tasks:
                # Fire and forget - don't await completion
                asyncio.create_task(asyncio.gather(*tasks, return_exceptions=True))
                
        except Exception as e:
            logger.error(f"Error setting up side effects for submission {submission_id}: {e}")


# Global side effect service instance
side_effect_service = SideEffectService()