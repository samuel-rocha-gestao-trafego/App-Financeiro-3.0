from app import create_app, db
import os

app = create_app()
with app.app_context():
    print("Iniciando sincronização do banco de dados...")
    try:
        db.create_all()
        print("Tabelas criadas/verificadas com sucesso!")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
