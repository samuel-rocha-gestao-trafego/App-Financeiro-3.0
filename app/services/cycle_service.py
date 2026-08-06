from datetime import date, timedelta
from decimal import Decimal
from calendar import monthrange
from app.extensions import db
from app.models.transaction import Transaction
from app.models.user_settings import UserSettings


class CycleService:

    @staticmethod
    def get_or_create_settings(user_id: int) -> UserSettings:
        """Retorna as configurações de ciclo do usuário ou cria com valores padrão."""
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id, cycle_day_1=5, cycle_day_2=20)
            db.session.add(settings)
            db.session.commit()
        return settings

    @staticmethod
    def update_cycle_settings(user_id: int, cycle_day_1: int, cycle_day_2: int) -> bool:
        """Atualiza os dias de ciclo do usuário."""
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
    def _get_cycle_date_ranges(cycle_day: int, reference_date: date):
        """
        Calcula o intervalo de datas (start, end) para um ciclo de pagamento.

        O ciclo que contém `reference_date` (hoje) começa no dia seguinte ao ciclo
        anterior e termina no `cycle_day` do mês correspondente.

        Exemplo com cycle_day=5 e reference_date=2026-08-06:
          - Este ciclo vai de 06/08 a 05/09
        Exemplo com cycle_day=5 e reference_date=2026-08-03:
          - Este ciclo vai de 06/07 a 05/08
        """
        today = reference_date
        current_day = today.day
        days_in_current_month = monthrange(today.year, today.month)[1]

        if current_day > cycle_day:
            # Estamos após o dia de pagamento → o ciclo atual vai até o próximo cycle_day
            start = date(today.year, today.month, cycle_day + 1) if cycle_day < days_in_current_month else date(today.year, today.month, 1)
            # Fim = cycle_day do mês seguinte
            next_month = today.month + 1
            next_year = today.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            end_day = min(cycle_day, monthrange(next_year, next_month)[1])
            end = date(next_year, next_month, end_day)
        else:
            # Estamos antes ou no dia de pagamento → o ciclo atual iniciou após o cycle_day anterior
            prev_month = today.month - 1
            prev_year = today.year
            if prev_month < 1:
                prev_month = 12
                prev_year -= 1
            # Início = dia seguinte ao cycle_day do mês anterior
            prev_days = monthrange(prev_year, prev_month)[1]
            start_day = min(cycle_day + 1, prev_days + 1)
            start = date(prev_year, prev_month, start_day)
            # Fim = cycle_day deste mês
            end_day = min(cycle_day, days_in_current_month)
            end = date(today.year, today.month, end_day)

        return start, end

    @staticmethod
    def get_cycle_data(user_id: int, cycle_day: int, reference_date: date, month: int, year: int):
        """
        Retorna os dados financeiros de um ciclo específico para o mês/ano selecionado.

        Para um dado mês/ano de visualização e um cycle_day, calcula:
          - Ciclo 1: do dia após o ciclo 2 do mês anterior até o cycle_day deste mês
          - Ciclo 2: do dia cycle_day+1 deste mês até o cycle_day (mas como estamos
                      filtrando pelo mês, consideramos de cycle_day+1 até o fim do mês
                      para o ciclo 2, e do início do mês até cycle_day para o ciclo 1)

        Na prática, para manter simplicidade e alinhado com o que o usuário pediu:
          - Cada transação é alocada ao ciclo baseado no seu dia de vencimento/recebimento
            dentro do mês selecionado.
          - Ciclo com day=X: transações cujo dia está entre (dia_anterior+1) e X
        """
        # Busca todas as transações do mês/ano para este usuário
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= date(year, month, 1),
            Transaction.date <= date(year, month, monthrange(year, month)[1])
        ).order_by(Transaction.date.asc()).all()

        # Separa receitas e despesas deste ciclo
        receitas = []
        despesas = []

        for t in transactions:
            if t.type == 'RECEITA' and t.date.day <= cycle_day:
                receitas.append(t)
            elif t.type == 'DESPESA' and t.date.day <= cycle_day:
                despesas.append(t)

        total_receitas = sum((t.amount for t in receitas), Decimal('0.00'))
        total_despesas = sum((t.amount for t in despesas), Decimal('0.00'))
        saldo = total_receitas - total_despesas

        return {
            'cycle_day': cycle_day,
            'receitas': receitas,
            'despesas': despesas,
            'total_receitas': float(total_receitas),
            'total_despesas': float(total_despesas),
            'saldo': float(saldo),
        }

    @staticmethod
    def get_both_cycles(user_id: int, month: int, year: int):
        """
        Retorna os dados dos dois ciclos para o mês/ano informado.

        Ciclo 1: transações com dia 1..cycle_day_1
        Ciclo 2: transações com dia (cycle_day_1+1)..cycle_day_2
        Transações com dia > cycle_day_2 são incluídas no ciclo 2 (período estendido
        até o fim do mês, já que não há um terceiro ciclo).
        """
        settings = CycleService.get_or_create_settings(user_id)
        cycle_day_1 = settings.cycle_day_1
        cycle_day_2 = settings.cycle_day_2

        # Busca todas as transações do mês/ano
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= date(year, month, 1),
            Transaction.date <= date(year, month, monthrange(year, month)[1])
        ).order_by(Transaction.date.asc()).all()

        # Separa por ciclo
        receitas_1, despesas_1 = [], []
        receitas_2, despesas_2 = [], []

        for t in transactions:
            dia = t.date.day
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
