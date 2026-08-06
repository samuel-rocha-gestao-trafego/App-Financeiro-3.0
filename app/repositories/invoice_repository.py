from typing import List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy import func
from app.extensions import db
from app.models.invoice import Invoice
from app.models.transaction import Transaction
from app.repositories.base_repository import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    model_class = Invoice

    @classmethod
    def get_or_create_for_month(cls, credit_card_id: int, user_id: int,
                                 month: int, year: int,
                                 closing_date: date, due_date: date) -> Invoice:
        """Busca fatura existente ou cria uma nova ABERTA."""
        invoice = Invoice.query.filter_by(
            credit_card_id=credit_card_id,
            month=month,
            year=year
        ).first()

        if not invoice:
            invoice = Invoice(
                credit_card_id=credit_card_id,
                user_id=user_id,
                month=month,
                year=year,
                closing_date=closing_date,
                due_date=due_date,
                status='ABERTA',
                total_amount=Decimal('0.00'),
                paid_amount=Decimal('0.00')
            )
            db.session.add(invoice)
            db.session.flush()

        return invoice

    @classmethod
    def recalculate_total(cls, invoice_id: int):
        """Recalcula total_amount somando transações vinculadas."""
        total = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.invoice_id == invoice_id
        ).scalar() or Decimal('0.00')

        invoice = Invoice.query.get(invoice_id)
        if invoice:
            invoice.total_amount = total
            db.session.commit()

    @classmethod
    def get_by_card_month(cls, credit_card_id: int, month: int, year: int) -> Optional[Invoice]:
        return Invoice.query.filter_by(
            credit_card_id=credit_card_id, month=month, year=year
        ).first()

    @classmethod
    def get_card_invoices(cls, credit_card_id: int) -> List[Invoice]:
        return Invoice.query.filter_by(
            credit_card_id=credit_card_id
        ).order_by(Invoice.year.desc(), Invoice.month.desc()).all()

    @classmethod
    def get_transactions(cls, invoice_id: int) -> List[Transaction]:
        return Transaction.query.filter_by(invoice_id=invoice_id).order_by(
            Transaction.transaction_date.desc()
        ).all()
