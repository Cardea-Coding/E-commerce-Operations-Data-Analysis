import os

import pytest

from app import create_app
from app.extensions import db
from app.services.sync_service import run_data_sync


@pytest.fixture(scope="session")
def app_instance():
    os.environ["DATABASE_URL"] = "sqlite:///test_phase5.db"
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        run_data_sync(source="mock_api", mode="manual")
    yield app


@pytest.fixture()
def client(app_instance):
    return app_instance.test_client()
