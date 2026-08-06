from decimal import Decimal
from sqlalchemy import extract, func
from app.extensions import db
from app.models.transaction import Transaction


class ReportService:

    @staticmethod
    def get_category_expenses_breakdown(user_id: int, month: int, year: int):
        """Retorna total gasto por categoria — usa transaction_date."""
        date_col = Transaction.transaction_date
        results = db.session.query(
            Transaction.category_id,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'DESPESA',
            Transaction.status == 'REALIZADO',
            extract('month', date_col) == month,
            extract('year', date_col) == year
        ).group_by(Transaction.category_id).all()

        return results

    @staticmethod
    def get_annual_evolution(user_id: int, year: int):
        """Evolução mensal — usa transaction_date."""
        date_col = Transaction.transaction_date
        monthly_data = []

        for month in range(1, 13):
            income = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'RECEITA',
                Transaction.status == 'REALIZADO',
                extract('month', date_col) == month,
                extract('year', date_col) == year
            ).scalar() or Decimal('0.00')

            expenses = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'DESPESA',
                Transaction.status == 'REALIZADO',
                extract('month', date_col) == month,
                extract('year', date_col) == year
            ).scalar() or Decimal('0.00')

            monthly_data.append({
                'month': month,
                'income': float(income),
                'expenses': float(expenses)
            })

        return monthly_data

    @staticmethod
    def get_cash_flow(user_id: int, month: int, year: int):
        """Fluxo de caixa: previsto vs realizado."""
        date_col = Transaction.transaction_date
        filters_base = [
            Transaction.user_id == user_id,
            extract('month', date_col) == month,
            extract('year', date_col) == year
        ]

        # Realizado
        realized_income = db.session.query(func.sum(Transaction.amount)).filter(
            *filters_base,
            Transaction.type == 'RECEITA',
            Transaction.status == 'REALIZADO'
        ).scalar() or Decimal('0.00')

        realized_expenses = db.session.query(func.sum(Transaction.amount)).filter(
            *filters_base,
            Transaction.type == 'DESPESA',
            Transaction.status == 'REALIZADO'
        ).scalar() or Decimal('0.00')

        # Previsto (total)
        predicted_income = db.session.query(func.sum(Transaction.amount)).filter(
            *filters_base,
            Transaction.type == 'RECEITA'
        ).scalar() or Decimal('0.00')

        predicted_expenses = db.session.query(func.sum(Transaction.amount)).filter(
            *filters_base,
            Transaction.type == 'DESPESA'
        ).scalar() or Decimal('0.00')

        return {
            'realized_income': realized_income,
            'realized_expenses': realized_expenses,
            'realized_balance': realized_income - realized_expenses,
            'predicted_income': predicted_income,
            'predicted_expenses': predicted_expenses,
            'predicted_balance': predicted_income - predicted_expenses,
        }
