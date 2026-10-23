"""Application factory and shared extensions."""
import os
import secrets
from datetime import timedelta
from pathlib import Path

import click
from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from sqlalchemy import event
from sqlalchemy.engine import Engine


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


@event.listens_for(Engine, 'connect')
def enable_sqlite_constraints(connection, _):
    if connection.__class__.__module__.startswith('sqlite3'):
        connection.execute('PRAGMA foreign_keys=ON')


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI='sqlite:///interntrack.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    # A persistent local secret avoids logging users out on every restart.
    # This file is runtime data and must never be packaged or committed.
    if not app.config.get('SECRET_KEY'):
        secret = os.environ.get('INTERNTRACK_SECRET_KEY')
        if not secret:
            secret_path = Path(app.instance_path) / 'secret.key'
            try:
                with open(secret_path, 'x', encoding='utf-8', opener=lambda p, f: os.open(p, f, 0o600)) as stream:
                    stream.write(secrets.token_hex(32))
            except FileExistsError:
                pass
            secret = secret_path.read_text().strip()
        if not secret:
            raise RuntimeError('INTERNTRACK_SECRET_KEY must not be empty.')
        app.config['SECRET_KEY'] = secret
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please sign in to continue.'
    from .models import User, STATUSES
    from .routes import main
    app.register_blueprint(main)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.context_processor
    def shared_context():
        return {'statuses': STATUSES}

    @app.after_request
    def headers(response):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template('error.html', code=400, message='This form expired or could not be verified. Reload the page and try again.'), 400

    for code, message in [(400, 'The request could not be processed.'), (404, 'This page or application could not be found.'), (413, 'This submission is too large.')]:
        def handler(error, code=code, message=message):
            return render_template('error.html', code=code, message=message), code
        app.register_error_handler(code, handler)

    @app.cli.command('init-db')
    def init_db():
        """Create missing tables without deleting existing records."""
        db.create_all()
        click.echo('Database ready. Existing records were preserved.')

    from .demo import seed_demo
    app.cli.add_command(seed_demo)
    return app
