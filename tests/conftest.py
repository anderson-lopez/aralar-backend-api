import pytest
from aralar.app import create_app
from mongomock import MongoClient as MockMongo


@pytest.fixture
def app(monkeypatch):
    app = create_app()
    # parchea Mongo a mongomock para tests
    from aralar import extensions

    mock_client = MockMongo()
    app.mongo_db = mock_client["aralar"]
    yield app


@pytest.fixture
def client(app):
    return app.test_client()
