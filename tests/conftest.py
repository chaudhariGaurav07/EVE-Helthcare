import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.database as database_module
from app.database import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

database_module.engine = test_engine


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "phone": "+919999999999",
    })
    resp = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers(client):
    client.post("/auth/signup", json={
        "email": "other@example.com",
        "password": "testpass123",
        "full_name": "Other User",
    })
    resp = client.post("/auth/login", json={
        "email": "other@example.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_centre(client, auth_headers):
    resp = client.post("/centres/", json={
        "name": "Test Diagnostics",
        "location": "Bangalore",
        "address": "MG Road, Bangalore",
    }, headers=auth_headers)
    return resp.json()


@pytest.fixture
def sample_test(client, auth_headers, sample_centre):
    resp = client.post(f"/centres/{sample_centre['id']}/tests", json={
        "name": "Blood Test",
        "description": "Basic blood test",
        "price": 500.00,
    }, headers=auth_headers)
    return resp.json()
