from datetime import date
from decimal import Decimal
from flask import flash
from app.extensions import db
from app.models.recurring_bill import RecurringBill
from app.repositories.recurring_repository import RecurringRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.transaction_service import TransactionService


class RecurringService:
    """
    Serviço de recorrência.

    Corrige bug P3: agora suporta RECEITA e DESPESA (antes sempre criava DESPESA).
    Usa o campo RecurringBill.type para determinar o tipo da transação gerada.
    """

    @staticmethod
    def generate_recurring_transactions(user_id: int):
        """
        Gera lançamentos previstos para recorrências ativas no mês corrente.
        """
        try:
            today = date.today()
            recurring_bills = RecurringRepository.get_active_by_user(user_id)

            for bill in recurring_bills:
                due_day = min(bill.due_day, 28)
                expected_date = date(today.year, today.month, due_day)

                # Verifica se já existe transação para este mês
                exists = TransactionRepository.exists_for_recurring_month(
                    user_id, bill.id, today.month, today.year
                )

                if not exists and expected_date >= bill.start_date:
                    if bill.end_date is None or expected_date <= bill.end_date:
                        TransactionService.create_transaction(
                            user_id=user_id,
                            trans_type=bill.type,  # Correção P3: usa bill.type
                            description=f'[Recorrente] {bill.description}',
                            amount=float(bill.amount),
                            transaction_date=expected_date,
                            account_id=bill.account_id,
                            category_id=bill.category_id,
                            credit_card_id=bill.credit_card_id,
                            status='PREVISTO',
                            is_recurring=True,
                            recurring_parent_id=bill.id,
                        )
        except Exception:
            db.session.rollback()
            flash('Erro ao processar contas recorrentes.', 'danger')

    @staticmethod
    def create_recurring_bill(user_id: int, description: str, amount: float,
                               frequency: str, due_day: int,
                               trans_type: str = 'DESPESA',
                               category_id: int = None, account_id: int = None,
                               credit_card_id: int = None) -> RecurringBill:
        """Cria uma nova regra de recorrência."""
        try:
            bill = RecurringBill(
                user_id=user_id,
                description=description,
                amount=Decimal(str(amount)),
                type=trans_type,
                frequency=frequency,
                due_day=due_day,
                category_id=category_id,
                account_id=account_id,
                credit_card_id=credit_card_id,
                start_date=date.today(),
                is_active=True
            )
            return RecurringRepository.save(bill)
        except Exception:
            db.session.rollback()
            flash('Erro ao criar recorrência.', 'danger')
            return None

    @staticmethod
    def delete_recurring_bill(bill_id: int, user_id: int):
        bill = RecurringRepository.get_by_id_and_user(bill_id, user_id)
        if bill:
            return RecurringRepository.delete(bill)
        return False
