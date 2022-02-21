from flask import render_template, redirect, url_for, request, flash
from werkzeug.urls import url_parse
from flask_login import login_user, current_user
from sqlalchemy.exc import OperationalError
from webservice.auth import bp
from webservice.auth.forms import LoginForm
from webservice.models import User


@bp.route('login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = None
        try:
            user = User.query.filter_by(username=form.username.data).first()
        except OperationalError as e:
            return render_template('errors/500.html', title='Ошибка соединения с базой данных')

        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя или пароль')
            return redirect(url_for('auth.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('core.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Вход в систему', form=form)
