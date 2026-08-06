from app import create_app, db
import os

app = create_app()
with app.app_context():
    print("Iniciando sincronização do banco de dados...")
    try:
        # 1) Cria tabelas que ainda não existem (invoices, installment_groups, etc.)
        db.create_all()
        print("[OK] db.create_all() — novas tabelas criadas")
    except Exception as e:
        print(f"[AVISO] db.create_all(): {e}")

    # 2) Migração de schema — adiciona colunas novas em tabelas existentes (PostgreSQL)
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        dialect = db.engine.dialect.name  # 'postgresql' ou 'sqlite'

        # --- transactions ---
        tx_cols = {c['name'] for c in inspector.get_columns('transactions')}

        col_defs_tx = [
            ('credit_card_id',       'INTEGER REFERENCES credit_cards(id) ON DELETE SET NULL'),
            ('invoice_id',           'INTEGER REFERENCES invoices(id) ON DELETE SET NULL'),
            ('installment_group_id', 'INTEGER REFERENCES installment_groups(id) ON DELETE SET NULL'),
            ('transaction_date',     'DATE NOT NULL DEFAULT CURRENT_DATE'),
            ('due_date',             'DATE'),
            ('payment_date',         'DATE'),
            ('competency_date',      'DATE'),
            ('payment_method',       'VARCHAR(20)'),
            ('status',               "VARCHAR(20) NOT NULL DEFAULT 'PREVISTO'"),
            ('installment_number',   'INTEGER'),
            ('attachment_path',      'VARCHAR(255)'),
        ]

        for col_name, col_type in col_defs_tx:
            if col_name not in tx_cols:
                sql = f'ALTER TABLE transactions ADD COLUMN {col_name} {col_type}'
                try:
                    db.session.execute(text(sql))
                    print(f'  [+] transactions.{col_name}')
                except Exception as e:
                    print(f'  [!] transactions.{col_name}: {e}')

        # Renomear recurring_bill_id -> recurring_parent_id (se existir)
        if 'recurring_bill_id' in tx_cols and 'recurring_parent_id' not in tx_cols:
            try:
                db.session.execute(text(
                    'ALTER TABLE transactions RENAME COLUMN recurring_bill_id TO recurring_parent_id'
                ))
                print('  [~] transactions.recurring_bill_id -> recurring_parent_id')
            except Exception as e:
                print(f'  [!] rename recurring_bill_id: {e}')
        elif 'recurring_parent_id' not in tx_cols:
            try:
                db.session.execute(text(
                    'ALTER TABLE transactions ADD COLUMN recurring_parent_id INTEGER REFERENCES recurring_bills(id) ON DELETE SET NULL'
                ))
                print('  [+] transactions.recurring_parent_id')
            except Exception as e:
                print(f'  [!] transactions.recurring_parent_id: {e}')

        # Migrar dados: date -> transaction_date/due_date/competency_date
        # Só atualiza linhas onde transaction_date ainda tem o valor DEFAULT (hoje)
        # e a coluna 'date' legada tem um valor diferente
        if 'date' in tx_cols and 'transaction_date' in tx_cols:
            try:
                db.session.execute(text(
                    "UPDATE transactions SET transaction_date = date, due_date = date, competency_date = date "
                    "WHERE date IS NOT NULL AND (transaction_date IS NULL OR transaction_date = CURRENT_DATE)"
                ))
                print('  [~] transactions: date copiada para transaction_date/due_date/competency_date')
            except Exception as e:
                print(f'  [!] migracao date: {e}')

        # Migrar dados: definir payment_method padrão
        if 'payment_method' in tx_cols:
            try:
                db.session.execute(text(
                    "UPDATE transactions SET payment_method = 'DINHEIRO' WHERE payment_method IS NULL"
                ))
                print('  [~] transactions: payment_method=DINHEIRO para nulos')
            except Exception as e:
                print(f'  [!] payment_method default: {e}')

        # --- credit_cards ---
        cc_cols = {c['name'] for c in inspector.get_columns('credit_cards')}
        cc_defs = [
            ('bank',      'VARCHAR(80)'),
            ('is_active', 'BOOLEAN NOT NULL DEFAULT TRUE'),
        ]
        for col_name, col_type in cc_defs:
            if col_name not in cc_cols:
                try:
                    db.session.execute(text(f'ALTER TABLE credit_cards ADD COLUMN {col_name} {col_type}'))
                    print(f'  [+] credit_cards.{col_name}')
                except Exception as e:
                    print(f'  [!] credit_cards.{col_name}: {e}')

        # --- recurring_bills ---
        rb_cols = {c['name'] for c in inspector.get_columns('recurring_bills')}

        # Renomear day_of_month -> due_day (se existir)
        if 'day_of_month' in rb_cols and 'due_day' not in rb_cols:
            try:
                db.session.execute(text('ALTER TABLE recurring_bills RENAME COLUMN day_of_month TO due_day'))
                print('  [~] recurring_bills.day_of_month -> due_day')
            except Exception as e:
                print(f'  [!] rename day_of_month: {e}')

        rb_defs = [
            ('account_id',     'INTEGER REFERENCES accounts(id) ON DELETE SET NULL'),
            ('credit_card_id', 'INTEGER REFERENCES credit_cards(id) ON DELETE SET NULL'),
            ('type',           "VARCHAR(20) NOT NULL DEFAULT 'DESPESA'"),
        ]
        for col_name, col_type in rb_defs:
            if col_name not in rb_cols:
                try:
                    db.session.execute(text(f'ALTER TABLE recurring_bills ADD COLUMN {col_name} {col_type}'))
                    print(f'  [+] recurring_bills.{col_name}')
                except Exception as e:
                    print(f'  [!] recurring_bills.{col_name}: {e}')

        db.session.commit()
        print('[OK] Migração de schema concluída com sucesso!')

    except Exception as e:
        db.session.rollback()
        print(f'[ERRO] Migração de schema: {e}')

    print('Sincronização finalizada. App pronta para receber requisições.')
