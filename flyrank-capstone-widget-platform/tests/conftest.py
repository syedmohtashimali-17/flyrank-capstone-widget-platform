import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base, get_db
from core.security import get_password_hash
from models.user import User
from models.widget import Widget
from models.submission import Submission
from services.geo_service import GeoService, MockGeoProvider
from main import app

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_b(db):
    """Create a second test user for tenant isolation tests."""
    user = User(
        email="testb@example.com", 
        password_hash=get_password_hash("testpassword123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "testpassword123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_b(client, test_user_b):
    """Get authentication headers for test user B."""
    response = client.post("/auth/login", json={
        "email": test_user_b.email,
        "password": "testpassword123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_widget(db, test_user):
    """Create a test widget."""
    widget = Widget(
        id="test-widget-123",
        owner_id=test_user.id,
        type="signup",
        title="Test Widget",
        description="Test Description",
        form_fields=[
            {
                "name": "name",
                "label": "Name",
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
        button_text="Submit",
        display_options={}
    )
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return widget


@pytest.fixture
def test_widget_b(db, test_user_b):
    """Create a test widget for user B."""
    widget = Widget(
        id="test-widget-b-456",
        owner_id=test_user_b.id,
        type="contact",
        title="Test Widget B",
        description="Test Description B",
        form_fields=[
            {
                "name": "message",
                "label": "Message",
                "type": "textarea",
                "required": True
            }
        ],
        button_text="Send",
        display_options={}
    )
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return widget


@pytest.fixture
def mock_geo_success():
    """Mock geo service that succeeds."""
    provider = MockGeoProvider(should_fail=False, response=("United States", "New York"))
    return GeoService([provider])


@pytest.fixture 
def mock_geo_fail_first():
    """Mock geo service where first provider fails, second succeeds."""
    provider_a = MockGeoProvider(should_fail=True)
    provider_b = MockGeoProvider(should_fail=False, response=("Canada", "Toronto"))
    return GeoService([provider_a, provider_b])


@pytest.fixture
def mock_geo_fail_all():
    """Mock geo service where all providers fail."""
    provider_a = MockGeoProvider(should_fail=True)
    provider_b = MockGeoProvider(should_fail=True)
    return GeoService([provider_a, provider_b])