from datetime import datetime, timedelta
import re
import pytest
from sqlalchemy import func
from interntrack import create_app, db
from interntrack.models import User, Application
from conftest import register, login, logout, token, add


def test_registration_hashing_and_authentication(app, client):
    response = register(client, 'Student')
    assert b'Your journey starts here' in response.data
    with app.app_context():
        user = db.session.scalar(db.select(User))
        assert user.username == 'student'
        assert user.password_hash != 'example-test-pass'
        assert user.check_password('example-test-pass')
    logout(client)
    response = login(client, password='wrong-password')
    assert b'Invalid username or password' in response.data
    assert client.get('/').status_code == 302
    assert b'Make every opportunity count' in login(client).data


def test_duplicate_case_insensitive_username(app, client):
    register(client)
    logout(client)
    response = register(client, 'STUDENT')
    assert b'username is already taken' in response.data
    with app.app_context():
        assert db.session.scalar(db.select(func.count()).select_from(User)) == 1


@pytest.mark.parametrize('username,password,confirm', [('ab','long-password','long-password'), ('bad name','long-password','long-password'), ('valid','short','short'), ('valid','long-password','different')])
def test_invalid_registration(app, client, username, password, confirm):
    client.post('/register', data={'csrf_token': token(client, '/register'), 'username': username, 'password': password, 'confirm': confirm})
    with app.app_context():
        assert db.session.scalar(db.select(func.count()).select_from(User)) == 0


def test_create_edit_delete_and_confirmation(app, client):
    register(client)
    response = add(client, job_url='https://example.com/job', notes='Prepare questions')
    assert b'Example Labs' in response.data and b'Prepare questions' in response.data
    assert b'Open job posting' in response.data
    with app.app_context():
        record = db.session.scalar(db.select(Application))
        record_id = record.id
        assert record.job_url == 'https://example.com/job'
    url = f'/applications/{record_id}'
    edit = client.post(url + '/edit', data={'csrf_token': token(client, url + '/edit'), 'company': 'Updated Company', 'position': 'Cloud Intern', 'applied_date': '2026-10-23', 'status': 'Offer', 'job_url': '', 'interview_datetime': '', 'notes': ''}, follow_redirects=True)
    assert b'Changes saved' in edit.data and b'Updated Company' in edit.data
    assert b'Remove this application?' in client.get(url + '/delete').data
    with app.app_context():
        assert db.session.get(Application, record_id) is not None
    deleted = client.post(url + '/delete', data={'csrf_token': token(client, url + '/delete')}, follow_redirects=True)
    assert b'Application deleted' in deleted.data
    assert client.get(url).status_code == 404


@pytest.mark.parametrize('changes', [{'company': ''}, {'company': '   '}, {'position': ''}, {'applied_date': 'bad-date'}, {'status': 'Invalid'}, {'job_url': 'javascript:alert(1)'}, {'job_url': 'https://user:pass@example.com'}, {'job_url': 'https://example.com:invalid'}, {'job_url': 'https://exa mple.com'}, {'interview_datetime':'invalid'}, {'notes':'x' * 5001}, {'company':'x' * 101}])
def test_invalid_application_does_not_save(app, client, changes):
    register(client)
    response = add(client, **changes)
    assert b'errors' in response.data
    with app.app_context():
        assert db.session.scalar(db.select(func.count()).select_from(Application)) == 0


def test_other_account_cannot_access_any_route_or_mutate(app, client):
    register(client, 'owner')
    add(client, notes='private-value-937')
    with app.app_context():
        record_id = db.session.scalar(db.select(Application.id))
    logout(client)
    register(client, 'other')
    assert b'Example Labs' not in client.get('/').data
    for suffix in ['', '/edit', '/delete']:
        assert client.get(f'/applications/{record_id}{suffix}').status_code == 404
    for suffix in ['/edit', '/delete']:
        response = client.post(f'/applications/{record_id}{suffix}', data={'csrf_token': token(client, '/'), 'company': 'Hacked'})
        assert response.status_code == 404
    with app.app_context():
        assert db.session.get(Application, record_id).notes == 'private-value-937'


@pytest.mark.parametrize('path', ['/register', '/login', '/logout', '/applications/new', '/applications/1/edit', '/applications/1/delete'])
def test_csrf_rejected(client, path):
    assert client.post(path, data={'csrf_token':'fake-token'}).status_code == 400
    assert client.post(path).status_code == 400


def test_csrf_rejection_preserves_existing_record(app, client):
    register(client)
    add(client)
    with app.app_context():
        record_id = db.session.scalar(db.select(Application.id))
    assert client.post(f'/applications/{record_id}/delete').status_code == 400
    with app.app_context():
        assert db.session.get(Application, record_id) is not None


@pytest.mark.parametrize('path', ['/', '/applications/new', '/applications/1', '/applications/1/edit', '/applications/1/delete'])
def test_protected_pages_redirect_to_login(client, path):
    response = client.get(path)
    assert response.status_code == 302 and '/login' in response.location


def test_search_filter_counts_literal_wildcards_and_pagination(app, client):
    register(client)
    add(client, company='Northstar', position='Cloud Intern', status='Interview')
    add(client, company='Harbor', status='Offer')
    add(client, company='100% Real', status='Applied')
    assert b'Northstar' in client.get('/?q=cLoUd').data
    assert b'Harbor' not in client.get('/?q=cLoUd').data
    assert b'Northstar' not in client.get('/?status=Offer').data
    assert b'Harbor' in client.get('/?status=Offer').data
    assert b'Northstar' not in client.get('/?q=%25').data
    assert b'100% Real' in client.get('/?q=%25').data
    assert b'No matching applications' in client.get('/?q=unmatched').data
    with app.app_context():
        user = db.session.scalar(db.select(User))
        for i in range(12):
            db.session.add(Application(user_id=user.id, company=f'Extra {i}', position='Developer', applied_date=datetime.now().date(), status='Applied'))
        db.session.commit()
    first = client.get('/')
    assert b'1 / 2' in first.data and b'of 15' in first.data
    assert b'2 / 2' in client.get('/?page=2').data
    assert b'1 / 2' in client.get('/?page=bad').data
    assert b'1 / 2' in client.get('/?page=-1').data
    assert b'2 / 2' in client.get('/?page=999').data


def test_upcoming_interviews_excludes_past_and_inactive(client):
    register(client)
    future = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M')
    past = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M')
    add(client, company='Future Interview', status='Interview', interview_datetime=future)
    add(client, company='Past Interview', status='Interview', interview_datetime=past)
    add(client, company='Closed Interview', status='Rejected', interview_datetime=future)
    response = client.get('/')
    rail = response.data.split(b'<aside class="right-rail">')[1]
    assert b'Future Interview' in rail
    assert b'Past Interview' not in rail and b'Closed Interview' not in rail


def test_no_open_redirect_and_no_html_execution(client):
    register(client)
    add(client, company='<script>alert(1)</script>', notes='<img src=x onerror=alert(1)>')
    response = client.get('/')
    assert b'<script>alert(1)</script>' not in response.data
    assert b'&lt;script&gt;' in response.data
    logout(client)
    data = {'csrf_token': token(client, '/login'), 'username': 'student', 'password': 'example-test-pass'}
    response = client.post('/login?next=https://evil.example', data=data)
    assert response.location == '/'
    assert "script-src 'self'" in response.headers['Content-Security-Policy']
    assert response.headers['Cache-Control'] == 'no-store'


def test_restart_persistence(app, client):
    register(client)
    add(client, notes='survives-restart')
    logout(client)
    assert b'Make every opportunity count' in login(client).data
    restarted = create_app({'TESTING': True, 'SECRET_KEY': 'test-only-key', 'SQLALCHEMY_DATABASE_URI': app.config['SQLALCHEMY_DATABASE_URI']})
    new_client = restarted.test_client()
    login(new_client)
    assert b'Example Labs' in new_client.get('/').data
    with restarted.app_context():
        assert db.session.scalar(db.select(Application)).notes == 'survives-restart'
        db.session.remove()
        db.engine.dispose()


def test_seed_demo_is_explicit_additive_and_password_checked(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=['seed-demo', '--password', 'demo-test-password'])
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.scalar(db.select(func.count()).select_from(Application)) == 7
    repeated = runner.invoke(args=['seed-demo', '--password', 'demo-test-password'])
    assert repeated.exit_code != 0 and 'already exists' in repeated.output
    with app.app_context():
        assert db.session.scalar(db.select(func.count()).select_from(Application)) == 7
    assert runner.invoke(args=['seed-demo', '--username', 'newdemo', '--password', 'short']).exit_code != 0


def test_init_db_does_not_drop_data(app, client):
    register(client)
    add(client)
    assert app.test_cli_runner().invoke(args=['init-db']).exit_code == 0
    with app.app_context():
        assert db.session.scalar(db.select(func.count()).select_from(Application)) == 1


def test_dashboard_status_totals(client):
    register(client)
    for status in ['Applied', 'Applied', 'Interview', 'Offer', 'Rejected', 'Withdrawn']:
        add(client, status=status)
    response = client.get('/?q=notfound')
    html = response.data.decode()
    assert re.search(r'Total applications.*?<strong>6</strong>', html, re.S)
    for status, number in [('Applied', 2), ('Interview', 1), ('Offer', 1), ('Rejected', 1), ('Withdrawn', 1)]:
        assert re.search(r'class="stat ' + status.lower() + r' .*?<strong>' + str(number) + '</strong>', html, re.S)


def test_first_start_creates_secret_and_restart_reuses_it(tmp_path, monkeypatch):
    """Exercise real first-run config; other fixtures provide a secret explicitly."""
    import interntrack
    from flask import Flask as RealFlask
    instance = tmp_path / 'fresh-instance'
    def isolated_flask(*args, **kwargs):
        kwargs['instance_path'] = str(instance)
        return RealFlask(*args, **kwargs)
    monkeypatch.setattr(interntrack, 'Flask', isolated_flask)
    monkeypatch.delenv('INTERNTRACK_SECRET_KEY', raising=False)
    first = interntrack.create_app({'TESTING': True})
    secret_path = instance / 'secret.key'
    assert secret_path.exists()
    assert len(first.config['SECRET_KEY']) == 64
    with first.app_context():
        db.create_all()
    assert first.test_client().get('/login').status_code == 200
    second = interntrack.create_app({'TESTING': True})
    assert second.config['SECRET_KEY'] == first.config['SECRET_KEY']
    for application in [first, second]:
        with application.app_context():
            db.session.remove()
            db.engine.dispose()
