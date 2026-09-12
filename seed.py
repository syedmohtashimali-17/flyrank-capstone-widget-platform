#!/usr/bin/env python3
"""Seed script to populate the database with sample data."""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine, Base
from core.security import get_password_hash
from models.user import User
from models.widget import Widget  
from models.submission import Submission
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_users(db: Session) -> tuple:
    """Create sample users."""
    logger.info("Creating sample users...")
    
    # User A
    user_a = User(
        email="owner_a@example.com",
        password_hash=get_password_hash("password123")
    )
    
    # User B  
    user_b = User(
        email="owner_b@example.com", 
        password_hash=get_password_hash("password123")
    )
    
    db.add(user_a)
    db.add(user_b)
    db.commit()
    db.refresh(user_a)
    db.refresh(user_b)
    
    logger.info(f"Created User A (ID: {user_a.id}): {user_a.email}")
    logger.info(f"Created User B (ID: {user_b.id}): {user_b.email}")
    
    return user_a, user_b


def create_sample_widgets(db: Session, user_a: User, user_b: User) -> dict:
    """Create sample widgets for both users."""
    logger.info("Creating sample widgets...")
    
    widgets = {}
    
    # User A widgets
    widgets['a_signup'] = Widget(
        id=str(uuid.uuid4()),
        owner_id=user_a.id,
        type="signup",
        title="Join Our Newsletter",
        description="Get the latest updates and product news delivered to your inbox.",
        form_fields=[
            {
                "name": "name",
                "label": "Full Name",
                "type": "text",
                "required": True
            },
            {
                "name": "email",
                "label": "Email Address", 
                "type": "email",
                "required": True
            },
            {
                "name": "company",
                "label": "Company",
                "type": "text",
                "required": False
            }
        ],
        button_text="Subscribe Now",
        display_options={
            "position": "bottom-right",
            "theme": "light"
        }
    )
    
    widgets['a_contact'] = Widget(
        id=str(uuid.uuid4()),
        owner_id=user_a.id,
        type="contact",
        title="Contact Us",
        description="Have a question? We'd love to hear from you.",
        form_fields=[
            {
                "name": "name",
                "label": "Your Name",
                "type": "text",
                "required": True
            },
            {
                "name": "email",
                "label": "Email",
                "type": "email", 
                "required": True
            },
            {
                "name": "subject",
                "label": "Subject",
                "type": "text",
                "required": True
            },
            {
                "name": "message",
                "label": "Message",
                "type": "textarea",
                "required": True
            }
        ],
        button_text="Send Message",
        display_options={
            "position": "center",
            "theme": "blue"
        }
    )
    
    # User B widgets
    widgets['b_signup'] = Widget(
        id=str(uuid.uuid4()),
        owner_id=user_b.id,
        type="signup",
        title="Early Access Program",
        description="Be among the first to try our new features.",
        form_fields=[
            {
                "name": "email",
                "label": "Email Address",
                "type": "email",
                "required": True
            },
            {
                "name": "role",
                "label": "Job Role",
                "type": "text",
                "required": False
            }
        ],
        button_text="Get Early Access",
        display_options={
            "position": "top-banner"
        }
    )
    
    widgets['b_cta'] = Widget(
        id=str(uuid.uuid4()),
        owner_id=user_b.id,
        type="cta",
        title="Download Our Guide",
        description="Free 25-page guide to modern web development.",
        form_fields=[
            {
                "name": "name",
                "label": "First Name",
                "type": "text", 
                "required": True
            },
            {
                "name": "email",
                "label": "Work Email",
                "type": "email",
                "required": True
            }
        ],
        button_text="Download Now",
        display_options={
            "position": "modal",
            "trigger": "exit-intent"
        }
    )
    
    # Add all widgets to database
    for widget in widgets.values():
        db.add(widget)
    
    db.commit()
    
    for key, widget in widgets.items():
        db.refresh(widget)
        logger.info(f"Created widget {key} (ID: {widget.id}): {widget.title}")
    
    return widgets


def create_sample_submissions(db: Session, widgets: dict) -> None:
    """Create sample submissions with varied dates and geographic data."""
    logger.info("Creating sample submissions...")
    
    base_date = datetime.utcnow() - timedelta(days=30)
    
    # Sample geographic locations
    geo_data = [
        ("United States", "New York"),
        ("United States", "San Francisco"), 
        ("Canada", "Toronto"),
        ("United Kingdom", "London"),
        ("Germany", "Berlin"),
        ("France", "Paris"),
        ("Japan", "Tokyo"),
        ("Australia", "Sydney"),
        ("Pakistan", "Karachi"),
        ("Pakistan", "Lahore"),
        ("India", "Mumbai"),
        ("Brazil", "São Paulo")
    ]
    
    # Sample IPs (fake but realistic)
    sample_ips = [
        "192.168.1.100", "10.0.0.50", "172.16.0.25",
        "203.0.113.45", "198.51.100.123", "93.184.216.34"
    ]
    
    # Sample user agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
    
    submissions_data = [
        # User A signup widget submissions
        (widgets['a_signup'], {
            "name": "John Smith",
            "email": "john.smith@example.com", 
            "company": "Tech Corp"
        }),
        (widgets['a_signup'], {
            "name": "Sarah Johnson",
            "email": "sarah.j@example.com",
            "company": "StartupXYZ"
        }),
        (widgets['a_signup'], {
            "name": "Mike Chen",
            "email": "mike.chen@example.com", 
            "company": ""
        }),
        (widgets['a_signup'], {
            "name": "Emily Davis",
            "email": "emily.davis@example.com",
            "company": "Design Studio"
        }),
        (widgets['a_signup'], {
            "name": "Ahmed Hassan", 
            "email": "ahmed.hassan@example.com",
            "company": "DevCorp"
        }),
        
        # User A contact widget submissions  
        (widgets['a_contact'], {
            "name": "Lisa Wong",
            "email": "lisa.wong@example.com",
            "subject": "Partnership Inquiry",
            "message": "We're interested in exploring partnership opportunities."
        }),
        (widgets['a_contact'], {
            "name": "David Brown",
            "email": "david.brown@example.com", 
            "subject": "Technical Support",
            "message": "Having trouble with the API integration."
        }),
        
        # User B signup widget submissions
        (widgets['b_signup'], {
            "email": "alex.miller@example.com",
            "role": "Product Manager"
        }),
        (widgets['b_signup'], {
            "email": "jessica.taylor@example.com",
            "role": "Software Engineer"
        }),
        (widgets['b_signup'], {
            "email": "carlos.rodriguez@example.com",
            "role": "Designer"
        }),
        
        # User B CTA widget submissions
        (widgets['b_cta'], {
            "name": "Maria",
            "email": "maria.garcia@example.com"
        }),
        (widgets['b_cta'], {
            "name": "James",
            "email": "james.wilson@example.com"
        })
    ]
    
    # Create submissions with varied dates
    for i, (widget, data) in enumerate(submissions_data):
        # Distribute submissions over the past 30 days
        days_ago = (i % 30)
        created_at = base_date + timedelta(days=days_ago, hours=(i % 24))
        
        # Pick geographic data
        country, city = geo_data[i % len(geo_data)]
        ip = sample_ips[i % len(sample_ips)]
        user_agent = user_agents[i % len(user_agents)]
        
        submission = Submission(
            widget_id=widget.id,
            tenant_id=widget.owner_id,
            submitted_data=data,
            ip_address=ip,
            country=country,
            city=city,
            user_agent=user_agent,
            created_at=created_at
        )
        
        db.add(submission)
    
    db.commit()
    logger.info(f"Created {len(submissions_data)} sample submissions")


def main():
    """Main seed function."""
    logger.info("Starting database seeding...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - be careful!)
        logger.info("Clearing existing data...")
        db.query(Submission).delete()
        db.query(Widget).delete()
        db.query(User).delete()
        db.commit()
        
        # Create sample data
        user_a, user_b = create_sample_users(db)
        widgets = create_sample_widgets(db, user_a, user_b)
        create_sample_submissions(db, widgets)
        
        logger.info("Database seeding completed successfully!")
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("SEED DATA SUMMARY")
        logger.info("="*50)
        logger.info("Users created:")
        logger.info(f"  • owner_a@example.com (password: password123)")
        logger.info(f"  • owner_b@example.com (password: password123)")
        logger.info("\nWidgets created:")
        for key, widget in widgets.items():
            logger.info(f"  • {widget.title} ({widget.type}) - ID: {widget.id}")
        logger.info(f"\nTotal submissions: {db.query(Submission).count()}")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()