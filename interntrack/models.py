"""Database models: every application belongs to exactly one user."""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

STATUSES = ('Applied', 'Interview', 'Offer', 'Rejected', 'Withdrawn')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    company = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(150), nullable=False)
    applied_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Applied')
    job_url = db.Column(db.String(1000), nullable=False, default='')
    interview_datetime = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=False, default='')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    __table_args__ = (db.CheckConstraint("status IN ('Applied','Interview','Offer','Rejected','Withdrawn')", name='valid_status'),)
