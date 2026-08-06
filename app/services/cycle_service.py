from datetime import date
from decimal import Decimal
from calendar import monthrange
from app.models.user_settings import UserSettings
from app.models.transaction import Transaction
from app.extensions import db


class CycleService:
    """
    Serviço de ciclos de pagamento.

    Usa transaction_date em vez do legado 'date'.
    Mantém compatibilidade com UserSettings existente.
    """

    @staticmethod
    def get_or_create_settings(user_id: int) -> UserSettings:
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id, cycle_day_1=5, cycle_day_2=20)
            db.session.add(settings)
            db.session.commit()
        return settings

    @staticmethod
    def update_cycle_settings(user_id: int, cycle_day_1: int, cycle_day_2: int) -> bool:
        try:
            settings = CycleService.get_or_create_settings(user_id)
            settings.cycle_day_1 = max(1, min(31, cycle_day_1))
            settings.cycle_day_2 = max(1, min(31, cycle_day_2))
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_both_cycles(user_id: int, month: int, year: int):
        """
        Retorna dados dos dois ciclos para o mês/ano.

        Ciclo 1: transações com dia 1..cycle_day_1
        Ciclo 2: transações com dia (cycle_day_1+1)..fim do mês
        """
        settings = CycleService.get_or_create_settings(user_id)
        cycle_day_1 = settings.cycle_day_1
        cycle_day_2 = settings.cycle_day_2

        # Busca transações usando transaction_date (novo campo)
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= date(year, month, 1),
            Transaction.transaction_date <= date(year, month, monthrange(year, month)[1])
        ).order_by(Transaction.transaction_date.asc()).all()

        receitas_1, despesas_1 = [], []
        receitas_2, despesas_2 = [], []

        for t in transactions:
            # Usar transaction_date, com fallback para date (legacy)
            t_date = t.transaction_date or t.date
            if not t_date:
                continue
            dia = t_date.day

            if t.type == 'RECEITA':
                if dia <= cycle_day_1:
                    receitas_1.append(t)
                else:
                    receitas_2.append(t)
            elif t.type == 'DESPESA':
                if dia <= cycle_day_1:
                    despesas_1.append(t)
                else:
                    despesas_2.append(t)

        def _totals(recs, desps):
            tr = sum((t.amount for t in recs), Decimal('0.00'))
            td = sum((t.amount for t in desps), Decimal('0.00'))
            return {
                'receitas': recs,
                'despesas': desps,
                'total_receitas': float(tr),
                'total_despesas': float(td),
                'saldo': float(tr - td),
            }

        ciclo1 = _totals(receitas_1, despesas_1)
        ciclo2 = _totals(receitas_2, despesas_2)

        return {
            'cycle_day_1': cycle_day_1,
            'cycle_day_2': cycle_day_2,
            'ciclo1': ciclo1,
            'ciclo2': ciclo2,
        }
