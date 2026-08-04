import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()


class Config:
    """Configurações base da aplicação."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_fallback_change_in_production')
    
    # Ajuste de URL para compatibilidade com SQLAlchemy caso comece com postgres://
    db_url = os.getenv('DATABASE_URL', 'sqlite:///financontrol.db')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
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
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}