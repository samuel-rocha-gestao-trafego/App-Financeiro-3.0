from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date
from sqlalchemy import extract, func, and_, or_
from app.extensions import db
from app.models.transaction import Transaction
from app.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    model_class = Transaction

    @classmethod
    def get_by_user_filtered(cls, user_id: int, start_date=None, end_date=None,
                             category_id=None, account_id=None, trans_type=None,
                             status=None, payment_method=None, search=None,
                             credit_card_id=None, invoice_id=None) -> List[Transaction]:
        """Busca transações com filtros compostos."""
        query = Transaction.query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if account_id:
            query = query.filter_by(account_id=account_id)
        if trans_type:
            query = query.filter_by(type=trans_type)
        if status:
            query = query.filter_by(status=status)
        if payment_method:
            query = query.filter_by(payment_method=payment_method)
        if credit_card_id:
            query = query.filter_by(credit_card_id=credit_card_id)
        if invoice_id:
            query = query.filter_by(invoice_id=invoice_id)
        if search:
            query = query.filter(Transaction.description.ilike(f'%{search}%'))
        return query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).all()

    @classmethod
    def get_by_month(cls, user_id: int, month: int, year: int, status=None) -> List[Transaction]:
        """Retorna transações de um mês/ano específico."""
        filters = [
            Transaction.user_id == user_id,
            extract('month', Transaction.transaction_date) == month,
            extract('year', Transaction.transaction_date) == year
        ]
        if status:
            filters.append(Transaction.status == status)
        return Transaction.query.filter(*filters).order_by(Transaction.transaction_date.desc()).all()

    @classmethod
    def get_by_date_range(cls, user_id: int, start: date, end: date) -> List[Transaction]:
        """Retorna transações em um intervalo de datas."""
        return Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end
        ).order_by(Transaction.transaction_date.asc()).all()

    @classmethod
    def get_realized_by_month(cls, user_id: int, month: int, year: int) -> List[Transaction]:
        """Transações realizadas (pagas) no mês — para cash flow."""
        return Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.status == 'REALIZADO',
            extract('month', Transaction.transaction_date) == month,
            extract('year', Transaction.transaction_date) == year
        ).all()

    @classmethod
    def sum_by_type_month(cls, user_id: int, month: int, year: int, trans_type: str, status=None) -> Decimal:
        """Soma valores de um tipo no mês."""
        filters = [
            Transaction.user_id == user_id,
            Transaction.type == trans_type,
            extract('month', Transaction.transaction_date) == month,
            extract('year', Transaction.transaction_date) == year
        ]
        if status:
            filters.append(Transaction.status == status)
        result = db.session.query(func.sum(Transaction.amount)).filter(*filters).scalar()
        return result or Decimal('0.00')

    @classmethod
    def get_by_installment_group(cls, group_id: int) -> List[Transaction]:
        return Transaction.query.filter_by(installment_group_id=group_id).order_by(Transaction.transaction_date.asc()).all()

    @classmethod
    def get_recurring_parent(cls, recurring_bill_id: int) -> Optional[Transaction]:
        """Busca a transação que serve como template de recorrência."""
        return Transaction.query.filter_by(recurring_parent_id=recurring_bill_id).first()

    @classmethod
    def exists_for_recurring_month(cls, user_id: int, recurring_parent_id: int, month: int, year: int) -> bool:
        """Verifica se já existe transação gerada para recorrência no mês."""
        return Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.recurring_parent_id == recurring_parent_id,
            Transaction.is_recurring == True,
            extract('month', Transaction.transaction_date) == month,
            extract('year', Transaction.transaction_date) == year
        ).first() is not None
