from decimal import Decimal
from sqlalchemy import extract, func
from app.extensions import db
from app.models.budget import Budget
from app.models.transaction import Transaction


class BudgetService:

    @staticmethod
    def get_category_budget_status(user_id: int, month: int, year: int):
        budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
        results = []

        for budget in budgets:
            # Soma todas as despesas da categoria no mês/ano selecionado
            spent = db.session.query(db.func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == budget.category_id,
                Transaction.type == 'DESPESA',
                Transaction.status == 'PAGO',
                extract('month', Transaction.date) == month,
                extract('year', Transaction.date) == year
            ).scalar() or Decimal('0.00')

            remaining = budget.planned_amount - spent
            percentage = (spent / budget.planned_amount * 100) if budget.planned_amount > 0 else 0

            results.append({
                'budget': budget,
                'category': budget.category,
                'planned': budget.planned_amount,
                'spent': spent,
                'remaining': remaining,
                'percentage': round(percentage, 1),
                'is_exceeded': spent > budget.planned_amount
            })

        return results