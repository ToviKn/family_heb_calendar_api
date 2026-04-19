import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure the application can import storage.database without failing.
os.environ.setdefault("DATABASE_URL", "sqlite:///./calendar_test_bootstrap.db")
os.environ["JWT_SECRET_KEY"] = "test-secret"

from main import app
from models.models import Family, FamilyMembership, User
from services.auth_service import create_access_token, hash_password
from storage.database import Base, get_db

TEST_DB_PATH = Path(__file__).parent / "test_suite.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def create_user_and_login(client: TestClient) -> Any:
    """Create a user via API and return a helper that logs in and returns auth data."""

    def _create_user_and_login(email: str, name: str, password: str) -> dict[str, Any]:
        create_response = client.post(
            "/users/",
            json={"email": email, "name": name, "password": password},
        )
        assert create_response.status_code == 200
        user_payload = create_response.json()

        login_response = client.post(
            "/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert login_response.status_code == 200
        login_payload = login_response.json()

        return {
            "user": user_payload,
            "access_token": login_payload["access_token"],
            "token_type": login_payload["token_type"],
        }

    return _create_user_and_login


@pytest.fixture(scope="function")
def sample_users(db_session: Session) -> dict[str, User]:
    owner = User(
        email="owner@example.com",
        name="Owner",
        password_hash=hash_password("owner-password"),
    )
    member = User(
        email="member@example.com",
        name="Member",
        password_hash=hash_password("member-password"),
    )
    outsider = User(
        email="outsider@example.com",
        name="Outsider",
        password_hash=hash_password("outsider-password"),
    )
    db_session.add_all([owner, member, outsider])
    db_session.commit()

    for user in (owner, member, outsider):
        db_session.refresh(user)

    return {"owner": owner, "member": member, "outsider": outsider}


@pytest.fixture(scope="function")
def auth_tokens(sample_users: dict[str, User]) -> dict[str, str]:
    return {
        "owner": create_access_token(sample_users["owner"].id),
        "member": create_access_token(sample_users["member"].id),
        "outsider": create_access_token(sample_users["outsider"].id),
    }


@pytest.fixture(scope="function")
def sample_family(db_session: Session, sample_users: dict[str, User]) -> Family:
    family = Family(name="Test Family")
    db_session.add(family)
    db_session.commit()
    db_session.refresh(family)

    owner_membership = FamilyMembership(
        user_id=sample_users["owner"].id,
        family_id=family.id,
        role="admin",
    )
    member_membership = FamilyMembership(
        user_id=sample_users["member"].id,
        family_id=family.id,
        role="member",
    )
    db_session.add_all([owner_membership, member_membership])
    db_session.commit()

    return family


@pytest.fixture(scope="function")
def event_payload(sample_family: Family, sample_users: dict[str, User]) -> dict[str, Any]:
    return {
        "title": "Family Dinner",
        "description": "Weekly family dinner",
        "calendar_type": "gregorian",
        "year": 2026,
        "month": 5,
        "day": 20,
        "repeat_type": "none",
        "family_id": sample_family.id,
    }


@pytest.fixture(scope="function")
def auth_header() -> Any:
    def _auth_header(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    return _auth_header
