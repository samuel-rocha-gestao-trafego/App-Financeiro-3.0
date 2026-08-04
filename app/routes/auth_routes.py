from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.account import Account
from app.services.recurring_service import RecurringService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        try:
            user = User.query.filter_by(email=username).first()
            if user and user.check_password(password):
                login_user(user, remember=True)
                RecurringService.generate_recurring_transactions(user.id)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                flash('E-mail ou senha incorretos.', 'danger')
        except Exception:
            flash('Erro ao autenticar. Tente novamente.', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Preencha todos os campos!', 'danger')
            return render_template('register.html')

        try:
            if User.query.filter_by(email=username).first():
                flash('E-mail já cadastrado.', 'danger')
            else:
                user = User(email=username, name=username)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()

                # Cria conta padrão "Carteira Principal" automaticamente
                conta_padrao = Account(
                    user_id=user.id,
                    name="Carteira Principal",
                    account_type="Carteira",
                    initial_balance=0.00,
                    current_balance=0.00,
                    color='#0d6efd',
                    icon='bi-wallet2'
                )
                db.session.add(conta_padrao)
                db.session.commit()

                flash('Conta criada com sucesso! Faça login.', 'success')
                return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('Erro ao criar conta. Tente novamente.', 'danger')

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão encerrada com segurança.', 'info')
    return redirect(url_for('auth.login'))
