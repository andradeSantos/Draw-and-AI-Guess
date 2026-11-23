"""Fixtures de integração usando banco PostgreSQL isolado (`draw_ia_test`)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import get_settings
from backend.app.core.database import Base, get_db
from backend.app.main import create_app


def _test_database_url() -> str:
    base_url = os.environ.get(
        "TEST_DATABASE_URL",
        get_settings().database_url,
    )
    if base_url.endswith("/draw_ia_db"):
        return base_url[: -len("/draw_ia_db")] + "/draw_ia_test"
    return base_url


@pytest.fixture(scope="session")
def test_engine():
    url = _test_database_url()
    # Garante que o banco draw_ia_test exista sem poluir draw_ia_db
    admin_url = url.rsplit("/", 1)[0] + "/draw_ia_db"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'draw_ia_test'")
        ).scalar()
        if not exists:
            conn.execute(text("CREATE DATABASE draw_ia_test"))
    admin_engine.dispose()

    engine = create_engine(url, pool_pre_ping=True, future=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(test_engine):
    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    # Limpa tabelas antes de cada teste para isolamento determinístico
    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE feedbacks, predictions CASCADE"))

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client
