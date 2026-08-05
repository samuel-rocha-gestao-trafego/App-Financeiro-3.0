from datetime import date
from decimal import Decimal
from flask import flash
from app.extensions import db
from app.models.recurring_bill import RecurringBill
from app.services.transaction_service import TransactionService


class RecurringService:

    @staticmethod
    def generate_recurring_transactions(user_id: int):
        """
        Verifica contas recorrentes ativas e gera lançamentos pendentes
        para o mês corrente caso ainda não tenham sido gerados.
        Substitui a função antiga gerar_lancamentos_recorrentes do app.py monolítico.
        """
        try:
            today = date.today()
            recurring_bills = RecurringBill.query.filter_by(user_id=user_id, is_active=True).all()

            for bill in recurring_bills:
                # Garante que o dia de vencimento seja válido para o mês atual
                due_day = min(bill.due_day, 28)
                expected_date = date(today.year, today.month, due_day)

                # Verifica se já existe um lançamento gerado para este mês
                exists = any(
                    t.date.month == today.month and t.date.year == today.year
                    for t in bill.generated_transactions
                )

                if not exists and expected_date >= bill.start_date:
                    if bill.end_date is None or expected_date <= bill.end_date:
                        TransactionService.create_transaction(
                            user_id=user_id,
                            account_id=bill.account_id,
                            category_id=bill.category_id,
                            trans_type='DESPESA',
                            description=f"[Recorrente] {bill.description}",
                            amount=float(bill.amount),
                            trans_date=expected_date,
                            status='PENDENTE',
                            recurring_bill_id=bill.id
                        )
        except Exception:
            db.session.rollback()
            flash('Erro ao processar contas recorrentes.', 'danger')

    @staticmethod
    def create_recurring_bill(user_id: int, description: str, amount: float, frequency: str, due_day: int, category_id: int = None, account_id: int = None):
        """Cria uma nova conta recorrente."""
        try:
            bill = RecurringBill(
                user_id=user_id,
                description=description,
                amount=Decimal(str(amount)),
                frequency=frequency,
                due_day=due_day,
                category_id=category_id,
                account_id=account_id,
                start_date=date.today(),
                is_active=True
            )
            db.session.add(bill)
            db.session.commit()
            return bill
        except Exception:
            db.session.rollback()
            flash('Erro ao criar conta recorrente.', 'danger')
            return None

    @staticmethod
    def delete_recurring_bill(bill_id: int, user_id: int):
        """Elimina uma conta recorrente."""
        try:
            bill = RecurringBill.query.filter_by(id=bill_id, user_id=user_id).first()
            if bill:
                db.session.delete(bill)
                db.session.commit()
                return True
            return False
        except Exception:
            db.session.rollback()
            flash('Erro ao excluir conta recorrente.', 'danger')
            return False
