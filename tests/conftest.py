import re
import pytest
from interntrack import create_app, db


@pytest.fixture
def app(tmp_path):
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only-key', 'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(tmp_path / 'test.db')})
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def token(client, path):
    page = client.get(path)
    match = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', page.data)
    assert match, page.data.decode()
    return match.group(1).decode()


def register(client, username='student', password='example-test-pass'):
    return client.post('/register', data={'csrf_token': token(client, '/register'), 'username': username, 'password': password, 'confirm': password}, follow_redirects=True)


def logout(client):
    return client.post('/logout', data={'csrf_token': token(client, '/')}, follow_redirects=True)


def login(client, username='student', password='example-test-pass'):
    return client.post('/login', data={'csrf_token': token(client, '/login'), 'username': username, 'password': password}, follow_redirects=True)


def add(client, **updates):
    data = {'company': 'Example Labs', 'position': 'Security Intern', 'applied_date': '2026-10-22', 'status': 'Applied', 'job_url': '', 'notes': '', 'interview_datetime': ''}
    data.update(updates)
    data['csrf_token'] = token(client, '/applications/new')
    return client.post('/applications/new', data=data, follow_redirects=True)
