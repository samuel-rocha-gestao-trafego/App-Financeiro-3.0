from app import create_app, db
from sqlalchemy import inspect, text
import os

app = create_app()
with app.app_context():
    print("Iniciando sincronização do banco de dados...")
    try:
        db.create_all()
        print("Tabelas criadas/verificadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")

    # Migração manual: adiciona colunas que podem faltar em tabelas existentes
    inspector = inspect(db.engine)
    migrations = []

    # Colunas esperadas por tabela (apenas as que podem faltar por evolução do modelo)
    expected_columns = {
        'transactions': [
            ('credit_card_id', db.Integer),
            ('recurring_bill_id', db.Integer),
            ('attachment_path', db.String(255)),
        ],
        'credit_cards': [
            ('color', db.String(7)),
            ('bank', db.String(80)),
        ],
        'user_settings': [
            ('cycle_day_1', db.Integer),
            ('cycle_day_2', db.Integer),
        ],
    }

    for table_name, columns in expected_columns.items():
        if table_name in inspector.get_table_names():
            existing = [c['name'] for c in inspector.get_columns(table_name)]
            for col_name, col_type in columns:
                if col_name not in existing:
                    nullable = True
                    migrations.append(f"  ALTER TABLE {table_name} ADD COLUMN {col_name} {'VARCHAR(255)' if 'String' in str(col_type) else 'INTEGER'}")
                    try:
                        db.session.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {col_name} {"VARCHAR(255)" if "String" in str(col_type) else "INTEGER"}'))
                        print(f"  Coluna '{col_name}' adicionada à tabela '{table_name}'")
                    except Exception as e:
                        print(f"  Erro ao adicionar '{col_name}' em '{table_name}': {e}")

    if not migrations:
        print("Nenhuma migração necessária.")
    else:
        print(f"{len(migrations)} migração(ões) aplicada(s).")

    db.session.commit()
    print("Banco de dados pronto!")
