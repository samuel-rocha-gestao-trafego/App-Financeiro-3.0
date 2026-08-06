import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env APENAS do diretório do projeto
_base_dir = Path(__file__).resolve().parent.parent
load_dotenv(_base_dir / '.env')


class Config:
    """Configurações base da aplicação."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_fallback_change_in_production')
    
    # Ajuste de URL para compatibilidade com SQLAlchemy caso comece com postgres://
    db_url = os.getenv('DATABASE_URL', 'sqlite:///financontrol.db')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Validação básica da URL do banco
    if not db_url or not db_url.strip():
        db_url = 'sqlite:///financontrol.db'

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurações de Segurança de Sessão e Cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 86400 * 30  # 30 dias


class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento."""
    DEBUG = True


class ProductionConfig(Config):
    """Configurações para ambiente de produção."""
    DEBUG = False
    # SESSION_COOKIE_SECURE deve ser True apenas se usar HTTPS
    # No Railway, o proxy lida com HTTPS, mas o Flask pode não detectar.
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Trusted origins para CSRF no Railway
    WTF_CSRF_TRUSTED_ORIGINS = [
        "https://financeirodorocha.up.railway.app",
        "http://financeirodorocha.up.railway.app"
    ]


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
