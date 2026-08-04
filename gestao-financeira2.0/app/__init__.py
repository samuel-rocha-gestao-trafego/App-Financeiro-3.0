import os
from flask import Flask
from app.config import config_by_name
from app.extensions import db, login_manager, migrate, csrf


def create_app(config_name=None):
    app = Flask(__name__)

    # Configuração por ambiente
    env = os.getenv('FLASK_ENV', 'development')
    config_class = config_by_name.get(config_name or env, config_by_name['default'])
    app.config.from_object(config_class)

    # Inicializa as extensões
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Importa modelos para que o SQLAlchemy os detecte ao criar as tabelas
    from app.models import (  # noqa: F401
        User, Account, Category, Transaction,
        CreditCard, CardPurchase, RecurringBill, Budget, Goal
    )

    # Registra o carregador de utilizador
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Regista os Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import main_bp
    from app.routes.transaction_routes import transactions_bp
    from app.routes.account_routes import accounts_bp
    from app.routes.card_routes import cards_bp
    from app.routes.report_routes import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(reports_bp)

    # Configura login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "danger"

    # Cria as tabelas ao iniciar
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Erro ao sincronizar tabelas: {e}")

    return app
