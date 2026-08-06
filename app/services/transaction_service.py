from datetime import date
from decimal import Decimal
from flask import flash
from sqlalchemy import extract
from app.extensions import db
from app.models.transaction import Transaction
from app.services.account_service import AccountService


class TransactionService:

    @staticmethod
    def get_filtered_transactions(user_id: int, start_date=None, end_date=None, category_id=None, account_id=None, trans_type=None, status=None, search=None):
        query = Transaction.query.filter_by(user_id=user_id)

        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if account_id:
            query = query.filter_by(account_id=account_id)
        if trans_type:
            query = query.filter_by(type=trans_type)
        if status:
            query = query.filter_by(status=status)
        if search:
            query = query.filter(Transaction.description.ilike(f"%{search}%"))

        return query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()

    @staticmethod
    def create_transaction(user_id: int, account_id: int, category_id: int, trans_type: str, description: str, amount: float, trans_date: date, status: str = 'PAGO', notes: str = None, recurring_bill_id: int = None, credit_card_id: int = None):
        """Cria uma nova transação e ajusta o saldo da conta se estiver paga."""
        try:
            amount_decimal = Decimal(str(amount))

            transaction = Transaction(
                user_id=user_id,
                account_id=account_id,
                category_id=category_id,
                credit_card_id=credit_card_id,
                type=trans_type,
                description=description,
                amount=amount_decimal,
                date=trans_date,
                status=status,
                notes=notes,
                recurring_bill_id=recurring_bill_id
            )
            db.session.add(transaction)

            # Se for um lançamento confirmado/pago, reflete no saldo da conta
            if status == 'PAGO':
                if trans_type == 'RECEITA':
                    AccountService.adjust_balance(account_id, amount_decimal)
                elif trans_type == 'DESPESA':
                    AccountService.adjust_balance(account_id, -amount_decimal)

            db.session.commit()
            return transaction
        except Exception:
            db.session.rollback()
            flash('Erro ao criar lançamento. Tente novamente.', 'danger')
            return None

    @staticmethod
    def delete_transaction(transaction: Transaction):
        """Elimina uma transação e reverte o impacto no saldo se estiver paga."""
        try:
            if transaction.status == 'PAGO':
                if transaction.type == 'RECEITA':
                    AccountService.adjust_balance(transaction.account_id, -transaction.amount)
                elif transaction.type == 'DESPESA':
                    AccountService.adjust_balance(transaction.account_id, transaction.amount)

            db.session.delete(transaction)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Erro ao excluir lançamento. Tente novamente.', 'danger')

    @staticmethod
    def get_monthly_summary(user_id: int, month: int, year: int):
        """Retorna o resumo financeiro do mês/ano: receitas, despesas e saldo."""
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.status == 'PAGO',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).all()

        income = sum((t.amount for t in transactions if t.type == 'RECEITA'), Decimal('0.00'))
        expenses = sum((t.amount for t in transactions if t.type == 'DESPESA'), Decimal('0.00'))

        return {
            'income': income,
            'expenses': expenses,
            'balance': income - expenses
        }
