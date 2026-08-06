Migração de dados da arquitetura antiga para a nova.
Este script deve ser rodado UMA VEZ após aplicar as novas colunas via Flask-Migrate (flask db upgrade).

O que faz:
1. Preenche transaction_date, due_date, payment_date, competency_date a partir do legado 'date'
2. Mapeia status PAGO -> REALIZADO, PENDENTE -> PREVISTO
3. Mapeia credit_card_id -> payment_method = 'CARTAO_CREDITO'
4. Migra CardPurchases para InstallmentGroup + Transactions vinculadas a Invoices
5. Corrige RecurringBill para suportar type=RECEITA
6. Cria Invoices para transações de cartão existentes
7. Nao exclui tabelas antigas (feito manualmente apos validacao)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from decimal import Decimal
from calendar import monthrange

from app import create_app
from app.extensions import db
from app.models.transaction import Transaction
from app.models.card_purchase import CardPurchase
from app.models.credit_card import CreditCard
from app.models.recurring_bill import RecurringBill
from app.models.invoice import Invoice
from app.models.installment_group import InstallmentGroup


def migrate_transactions(app):
    with app.app_context():
        transactions = Transaction.query.all()
        count = 0
        for t in transactions:
            changed = False
            if t.date and not t.transaction_date:
                t.transaction_date = t.date
                t.due_date = t.date
                t.competency_date = t.date
                changed = True
            if t.status == 'PAGO':
                t.status = 'REALIZADO'
                t.payment_date = t.transaction_date or t.date
                changed = True
            elif t.status == 'PENDENTE':
                t.status = 'PREVISTO'
                changed = True
            if t.credit_card_id and not t.payment_method:
                t.payment_method = 'CARTAO_CREDITO'
                changed = True
            elif not t.payment_method:
                t.payment_method = 'DINHEIRO'
                changed = True
            if changed:
                count += 1
        db.session.commit()
        print(f'[OK] {count} transacoes migradas (datas, status, payment_method)')


def migrate_card_purchases(app):
    with app.app_context():
        purchases = CardPurchase.query.all()
        if not purchases:
            print('[SKIP] Nenhum CardPurchase para migrar')
            return
        count = 0
        for p in purchases:
            card = CreditCard.query.get(p.credit_card_id)
            if not card:
                continue
            group = InstallmentGroup(
                user_id=card.user_id,
                credit_card_id=p.credit_card_id,
                description=p.description,
                total_amount=p.total_amount,
                installments_count=p.installments_count,
                purchase_date=p.purchase_date
            )
            db.session.add(group)
            db.session.flush()
            installment_val = p.total_amount / Decimal(p.installments_count)
            for i in range(p.installments_count):
                total_m = (p.first_bill_month - 1 + i)
                m = (total_m % 12) + 1
                y = p.first_bill_year + (total_m // 12)
                dia = min(card.due_day, monthrange(y, m)[1])
                parcela_date = date(y, m, dia)
                closing_day = min(card.closing_day, monthrange(y, m)[1])
                invoice = Invoice.query.filter_by(
                    credit_card_id=card.id, month=m, year=y
                ).first()
                if not invoice:
                    invoice = Invoice(
                        credit_card_id=card.id,
                        user_id=card.user_id,
                        month=m, year=y,
                        closing_date=date(y, m, closing_day),
                        due_date=parcela_date,
                        status='ABERTA',
                        total_amount=Decimal('0.00')
                    )
                    db.session.add(invoice)
                    db.session.flush()
                desc = f'{p.description} ({i+1}/{p.installments_count})'
                t = Transaction(
                    user_id=card.user_id,
                    category_id=p.category_id,
                    credit_card_id=p.credit_card_id,
                    invoice_id=invoice.id,
                    installment_group_id=group.id,
                    installment_number=i + 1,
                    type='DESPESA',
                    description=desc,
                    amount=installment_val,
                    transaction_date=parcela_date,
                    due_date=parcela_date,
                    competency_date=parcela_date,
                    payment_method='CARTAO_CREDITO',
                    status='PREVISTO',
                    date=parcela_date,
                )
                db.session.add(t)
                invoice.total_amount += installment_val
            count += 1
        db.session.commit()
        print(f'[OK] {count} CardPurchases migrados para InstallmentGroup + Invoice')


def migrate_existing_card_transactions(app):
    with app.app_context():
        transactions = Transaction.query.filter(
            Transaction.payment_method == 'CARTAO_CREDITO',
            Transaction.invoice_id.is_(None),
            Transaction.transaction_date.isnot(None)
        ).all()
        if not transactions:
            print('[SKIP] Nenhuma transacao de cartao sem invoice')
            return
        count = 0
        for t in transactions:
            card = CreditCard.query.get(t.credit_card_id)
            if not card:
                continue
            td = t.transaction_date
            m, y = td.month, td.year
            if td.day >= card.closing_day:
                m += 1
                if m > 12:
                    m = 1
                    y += 1
            invoice = Invoice.query.filter_by(
                credit_card_id=card.id, month=m, year=y
            ).first()
            if not invoice:
                closing_day = min(card.closing_day, monthrange(y, m)[1])
                due_day = min(card.due_day, monthrange(y, m)[1])
                invoice = Invoice(
                    credit_card_id=card.id,
                    user_id=t.user_id,
                    month=m, year=y,
                    closing_date=date(y, m, closing_day),
                    due_date=date(y, m, due_day),
                    status='ABERTA',
                    total_amount=t.amount
                )
                db.session.add(invoice)
                db.session.flush()
            else:
                invoice.total_amount += t.amount
            t.invoice_id = invoice.id
            count += 1
        db.session.commit()
        print(f'[OK] {count} transacoes de cartao vinculadas a Invoices')


def migrate_recurring_bills(app):
    with app.app_context():
        bills = RecurringBill.query.filter(RecurringBill.type.is_(None)).all()
        for b in bills:
            b.type = 'DESPESA'
        if bills:
            db.session.commit()
            print(f'[OK] {len(bills)} RecurringBills atualizadas com type=DESPESA')
        else:
            print('[SKIP] Nenhuma RecurringBill sem type')


def main():
    print('=' * 60)
    print('MIGRACAO v2.0 — Arquitetura Unificada')
    print('=' * 60)
    app = create_app()
    with app.app_context():
        try:
            db.session.execute(db.text('SELECT transaction_date FROM transactions LIMIT 1'))
        except Exception:
            print('[ERRO] Colunas novas nao existem. Rode `flask db upgrade` primeiro.')
            return
    print()
    migrate_transactions(app)
    migrate_card_purchases(app)
    migrate_existing_card_transactions(app)
    migrate_recurring_bills(app)
    print()
    print('=' * 60)
    print('MIGRACAO CONCLUIDA')
    print('=' * 60)


if __name__ == '__main__':
    main()
