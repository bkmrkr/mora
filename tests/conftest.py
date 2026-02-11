"""Shared test fixtures — isolated temp DB for every test."""
import os
import sys
import tempfile

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    """Redirect DB_PATH to a temp file for every test."""
    db_path = str(tmp_path / 'test_mora.db')
    monkeypatch.setattr('config.settings.DB_PATH', db_path)

    # Also patch the already-imported database module
    import db.database as db_mod
    monkeypatch.setattr(db_mod, 'DB_PATH', db_path)

    from db.database import init_db
    init_db()

    return db_path


@pytest.fixture
def app(temp_db):
    """Flask test app."""
    from app import create_app
    application = create_app()
    application.config['TESTING'] = True
    return application


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
