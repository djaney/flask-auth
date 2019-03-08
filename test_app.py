import pytest
from app import app
import json


def pytest_namespace():
    return {'user_id': None, 'token': None}

@pytest.fixture
def client():
    return app.test_client()




def test_create_user(client):
    rv = client.post('/users/', data=json.dumps({
        "username": "tom",
        "email": "tom@test.com",
        "password": "ilovesnakes",
        "first_name": "Tom",
        "last_name": "Riddle"
    }), content_type="application/json")

    response = json.loads(rv.data.decode('utf-8'))

    assert "tom" == response["username"]
    assert "tom@test.com" == response["email"]
    assert "password" not in response.keys()
    assert "Tom" == response["first_name"]
    assert "Riddle" == response["last_name"]

    pytest.user_id = response['id']

def test_get_user(client):
    rv = client.get('/users/{}'.format(pytest.user_id), data=json.dumps({
        "username": "tom",
        "email": "tom@test.com",
        "password": "ilovesnakes",
        "first_name": "Tom",
        "last_name": "Riddle"
    }), content_type="application/json")

    response = json.loads(rv.data.decode('utf-8'))

    assert "tom" == response["username"]
    assert "tom@test.com" == response["email"]
    assert "password" not in response.keys()
    assert "Tom" == response["first_name"]
    assert "Riddle" == response["last_name"]


def test_get_token(client):
    rv = client.post('/jwt/', data=json.dumps({
        "username": "tom",
        "password": "ilovesnakes",
    }), content_type="application/json")

    response = json.loads(rv.data.decode('utf-8'))

    assert "token" in response.keys()
    pytest.token = response['token']


def test_validate_token(client):
    rv = client.get('/jwt/validate?token={}'.format(pytest.token))
    assert rv.status_code == 200

def test_validate_token_error(client):
    rv = client.get('/jwt/validate?token={}'.format("wrong token"))
    assert rv.status_code == 401