from decimal import Decimal
from sqlalchemy import extract, func
from app.extensions import db
from app.models.transaction import Transaction


class ReportService:

    @staticmethod
    def get_category_expenses_breakdown(user_id: int, month: int, year: int):
        """Retorna o total gasto agrupado por categoria para gráficos de rosca/pizza."""
        results = db.session.query(
            Transaction.category_id,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'DESPESA',
            Transaction.status == 'PAGO',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).group_by(Transaction.category_id).all()

        return results

    @staticmethod
    def get_annual_evolution(user_id: int, year: int):
        """Retorna receitas e despesas de cada mês do ano para o gráfico de evolução."""
        monthly_data = []

        for month in range(1, 13):
            income = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'RECEITA',
                Transaction.status == 'PAGO',
                extract('month', Transaction.date) == month,
                extract('year', Transaction.date) == year
            ).scalar() or Decimal('0.00')

            expenses = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.type == 'DESPESA',
                Transaction.status == 'PAGO',
                extract('month', Transaction.date) == month,
                extract('year', Transaction.date) == year
            ).scalar() or Decimal('0.00')

            monthly_data.append({
                'month': month,
                'income': float(income),
                'expenses': float(expenses)
            })

        return monthly_data