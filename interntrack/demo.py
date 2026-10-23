"""Explicit, additive sample-data command; never seeds a normal account."""
from datetime import date, datetime, timedelta
import getpass
import click
from flask.cli import with_appcontext
from . import db
from .models import User, Application


@click.command('seed-demo')
@click.option('--username', default='demo', help='New demo username; must not already exist.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Choose a demo password of 10-128 characters.')
@with_appcontext
def seed_demo(username, password):
    """Create a dedicated account containing clearly fictional sample records."""
    import re
    username = username.strip().lower()
    if not re.fullmatch(r'[a-z0-9_.-]{3,40}', username):
        raise click.ClickException('Username must contain 3-40 allowed characters.')
    if not 10 <= len(password) <= 128:
        raise click.ClickException('Password must contain 10-128 characters.')
    db.create_all()
    if db.session.scalar(db.select(User).where(User.username == username)):
        raise click.ClickException('That account already exists. Choose another username; no data was changed.')
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    examples = [
        ('Northstar Labs', 'Cloud Security Intern', 'Interview', 4),
        ('Maple Systems', 'Software Engineering Intern', 'Applied', None),
        ('Harbor Analytics', 'IT Support Intern', 'Offer', None),
        ('Summit Networks', 'Network Security Intern', 'Applied', None),
        ('Cedar Digital', 'Application Security Intern', 'Rejected', None),
        ('Atlas Computing', 'Cloud Operations Intern', 'Interview', 2),
        ('Pioneer Software', 'Backend Development Intern', 'Withdrawn', None),
    ]
    for i, (company, position, status, days) in enumerate(examples):
        interview = (datetime.now() + timedelta(days=days)).replace(hour=10+i, minute=0, second=0, microsecond=0) if days else None
        db.session.add(Application(user_id=user.id, company=company, position=position, status=status, applied_date=date.today()-timedelta(days=i+1), interview_datetime=interview, notes='Fictional demonstration record. Replace with your own information when ready.'))
    db.session.commit()
    click.echo(f'Created {username} with 7 fictional applications. Sign in using your chosen password.')
