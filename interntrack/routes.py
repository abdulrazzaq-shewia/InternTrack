"""HTTP workflows. Ownership is checked server-side on every record route."""
from datetime import datetime
import math
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Application, STATUSES
from .forms import RegisterForm, LoginForm, ApplicationForm, ActionForm

main = Blueprint('main', __name__)
DUMMY_HASH = generate_password_hash('not-a-real-account-password')


def owned_application(application_id):
    return db.first_or_404(db.select(Application).where(Application.id == application_id, Application.user_id == current_user.id))


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.username.errors.append('This username is already taken.')
        else:
            session.clear()
            login_user(user)
            session.permanent = True
            flash('Your account is ready. Add your first application.', 'success')
            return redirect(url_for('main.dashboard'))
    return render_template('auth.html', form=form, mode='register')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.username == form.username.data))
        valid = user.check_password(form.password.data) if user else check_password_hash(DUMMY_HASH, form.password.data)
        if user and valid:
            session.clear()
            login_user(user)
            session.permanent = True
            return redirect(url_for('main.dashboard'))
        form.password.errors.append('Invalid username or password.')
    return render_template('auth.html', form=form, mode='login')


@main.post('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have signed out.', 'success')
    return redirect(url_for('main.login'))


@main.get('/')
@login_required
def dashboard():
    q = request.args.get('q', '').strip()[:150]
    status = request.args.get('status', '')
    if status not in STATUSES:
        status = ''
    base = db.select(Application).where(Application.user_id == current_user.id)
    filtered = base
    if q:
        filtered = filtered.where(or_(Application.company.icontains(q, autoescape=True), Application.position.icontains(q, autoescape=True)))
    if status:
        filtered = filtered.where(Application.status == status)
    total = db.session.scalar(db.select(func.count()).select_from(filtered.subquery()))
    pages = max(1, math.ceil(total / 10))
    page = min(max(request.args.get('page', 1, type=int) or 1, 1), pages)
    applications = db.session.scalars(filtered.order_by(Application.applied_date.desc(), Application.id.desc()).offset((page - 1) * 10).limit(10)).all()
    grouped = db.session.execute(db.select(Application.status, func.count()).where(Application.user_id == current_user.id).group_by(Application.status)).all()
    counts = {s: 0 for s in STATUSES}
    counts.update(dict(grouped))
    upcoming = db.session.scalars(base.where(Application.interview_datetime >= datetime.now(), Application.status == 'Interview').order_by(Application.interview_datetime, Application.id).limit(5)).all()
    return render_template('dashboard.html', applications=applications, counts=counts, upcoming=upcoming, total=total, page=page, pages=pages, q=q, status=status)


@main.route('/applications/new', methods=['GET', 'POST'])
@login_required
def create_application():
    form = ApplicationForm()
    if form.validate_on_submit():
        application = Application(user_id=current_user.id)
        form.populate_obj(application)
        db.session.add(application)
        db.session.commit()
        flash('Application added.', 'success')
        return redirect(url_for('main.detail', application_id=application.id))
    return render_template('application_form.html', form=form, application=None)


@main.get('/applications/<int:application_id>')
@login_required
def detail(application_id):
    return render_template('detail.html', application=owned_application(application_id))


@main.route('/applications/<int:application_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_application(application_id):
    application = owned_application(application_id)
    form = ApplicationForm(obj=application)
    if form.validate_on_submit():
        form.populate_obj(application)
        db.session.commit()
        flash('Changes saved.', 'success')
        return redirect(url_for('main.detail', application_id=application.id))
    return render_template('application_form.html', form=form, application=application)


@main.route('/applications/<int:application_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_application(application_id):
    application = owned_application(application_id)
    form = ActionForm()
    if form.validate_on_submit():
        db.session.delete(application)
        db.session.commit()
        flash('Application deleted.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('delete.html', application=application, form=form)
