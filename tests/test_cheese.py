import os
import pytest
from cheese.factory import create_app

@pytest.fixture
def app():
    app = create_app()
    app.testing = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_foo(client, app):
    rv = client.get('/')
    print rv.data
    assert False
