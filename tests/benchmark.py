"""Reproducible server-side timing; not a browser/network benchmark."""
import json
import platform
import statistics
import tempfile
from datetime import date
from pathlib import Path
from time import perf_counter
from interntrack import create_app, db
from interntrack.models import User, Application
from conftest import login


def run():
    with tempfile.TemporaryDirectory() as tmp:
        app = create_app({'TESTING': True, 'SECRET_KEY': 'benchmark-only', 'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(Path(tmp) / 'benchmark.db')})
        with app.app_context():
            db.create_all()
            user = User(username='student')
            user.set_password('example-test-pass')
            db.session.add(user)
            db.session.flush()
            for i in range(1000):
                db.session.add(Application(user_id=user.id, company=f'Example {i}', position='Cloud Intern', applied_date=date.today(), status='Applied'))
            db.session.commit()
        client = app.test_client()
        login(client)
        results = {}
        for label, path in [('dashboard', '/'), ('search', '/?q=Cloud&status=Applied')]:
            elapsed = []
            for _ in range(20):
                start = perf_counter()
                response = client.get(path)
                elapsed.append(round((perf_counter()-start)*1000, 3))
                assert response.status_code == 200
                assert b'of 1000' in response.data
            ordered = sorted(elapsed)
            results[label] = {'trials':20, 'median_ms':round(statistics.median(elapsed),3), 'p95_ms':ordered[18], 'max_ms':max(elapsed), 'under_2s':sum(t <= 2000 for t in elapsed), 'samples_ms':elapsed}
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        result = {'python':platform.python_version(), 'platform':platform.system()+' '+platform.machine(), 'records':1000, 'method':'Flask test client, sequential local server-side requests; excludes browser rendering and network time', 'results':results}
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    run()
