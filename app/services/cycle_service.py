from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
from calendar import monthrange
from sqlalchemy import extract
from app.extensions import db
from app.models.transaction import Transaction
from app.models.credit_card import CreditCard
from app.models.recurring_bill import RecurringBill
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
        """
        today = reference_date
        current_day = today.day
        days_in_current_month = monthrange(today.year, today.month)[1]

        if current_day > cycle_day:
            start = date(today.year, today.month, cycle_day + 1) if cycle_day < days_in_current_month else date(today.year, today.month, 1)
            next_month = today.month + 1
            next_year = today.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            end_day = min(cycle_day, monthrange(next_year, next_month)[1])
            end = date(next_year, next_month, end_day)
        else:
            prev_month = today.month - 1
            prev_year = today.year
            if prev_month < 1:
                prev_month = 12
                prev_year -= 1
            prev_days = monthrange(prev_year, prev_month)[1]
            start_day = min(cycle_day + 1, prev_days + 1)
            start = date(prev_year, prev_month, start_day)
            end_day = min(cycle_day, days_in_current_month)
            end = date(today.year, today.month, end_day)

        return start, end

    @staticmethod
    def _group_expenses_by_category(transactions):
        """
        Agrupa despesas por categoria para visão sintética.
        Retorna lista de dicts: {category_name, category_color, total, count, transactions}
        """
        groups = defaultdict(lambda: {'total': Decimal('0.00'), 'count': 0, 'transactions': [], 'category_name': 'Sem Categoria', 'category_color': '#6b7280'})

        for t in transactions:
            cat_name = t.category.name if t.category else 'Sem Categoria'
            cat_color = t.category.color if t.category else '#6b7280'
            key = cat_name
            groups[key]['category_name'] = cat_name
            groups[key]['category_color'] = cat_color
            groups[key]['total'] += t.amount
            groups[key]['count'] += 1
            groups[key]['transactions'].append(t)

        # Converte para lista ordenada pelo maior valor
        result = []
        for key, g in groups.items():
            result.append({
                'category_name': g['category_name'],
                'category_color': g['category_color'],
                'total': float(g['total']),
                'count': g['count'],
                'transactions': g['transactions']
            })
        result.sort(key=lambda x: x['total'], reverse=True)
        return result

    @staticmethod
    def _get_credit_card_bills(user_id: int, month: int, year: int):
        """
        Calcula o total da fatura de CADA cartão de crédito do usuário
        para o mês/ano, usando a tabela transactions (onde credit_card_id nao é nulo).
        Também identifica em qual ciclo o vencimento do cartão cai.
        Retorna lista de dicts com dados do cartão e valor da fatura.
        """
        cartoes = CreditCard.query.filter_by(user_id=user_id).all()
        bills = []

        for cartao in cartoes:
            # Soma todas as transações de despesa deste cartão no mês/ano
            # (exclui o lançamento de "Pagamento Fatura" que é uma DESPESA de conta corrente)
            transacoes_cartao = Transaction.query.filter(
                Transaction.user_id == user_id,
                Transaction.credit_card_id == cartao.id,
                Transaction.type == 'DESPESA',
                extract('month', Transaction.date) == month,
                extract('year', Transaction.date) == year
            ).all()

            # Exclui transações que são pagamentos de fatura (o próprio pagamento
            # é uma DESPESA na conta corrente, não no cartão)
            valor_fatura = sum(
                (t.amount for t in transacoes_cartao
                 if 'Pagamento' not in t.description and 'Fatura' not in t.description),
                Decimal('0.00')
            )

            if valor_fatura > 0:
                # Determina em qual ciclo o vencimento deste cartão cai
                # baseado no due_day do cartão
                bills.append({
                    'card_id': cartao.id,
                    'card_name': cartao.name,
                    'card_color': cartao.color,
                    'card_bank': cartao.bank or '',
                    'due_day': cartao.due_day,
                    'closing_day': cartao.closing_day,
                    'bill_total': float(valor_fatura),
                    'credit_limit': float(cartao.credit_limit or 0),
                    'item_count': len(transacoes_cartao)
                })

        return bills

    @staticmethod
    def _get_recurring_bills_for_month(user_id: int, month: int, year: int):
        """
        Busca contas recorrentes ativas e seus lançamentos gerados para o mês/ano.
        Retorna lista de dicts com info da conta recorrente, valor e vencimento.
        """
        recorrentes = RecurringBill.query.filter_by(user_id=user_id, is_active=True).all()
        result = []

        for bill in recorrentes:
            # Verifica se tem lançamento gerado para este mês
            tem_lancamento = any(
                t.date.month == month and t.date.year == year
                for t in bill.generated_transactions
            )

            if tem_lancamento:
                # Busca a transação gerada
                transacao = None
                for t in bill.generated_transactions:
                    if t.date.month == month and t.date.year == year:
                        transacao = t
                        break

                result.append({
                    'bill_id': bill.id,
                    'description': bill.description,
                    'amount': float(bill.amount),
                    'due_day': bill.due_day,
                    'frequency': bill.frequency,
                    'status': transacao.status if transacao else 'PENDENTE',
                    'transaction_id': transacao.id if transacao else None,
                    'category_name': transacao.category.name if transacao and transacao.category else 'Sem Categoria',
                    'account_name': bill.account.name if bill.account else None,
                })

        return result

    @staticmethod
    def _build_cycle(despesas_normais, receitas, faturas_cartao, cycle_day_1, cycle_day_2, cycle_num):
        """
        Monta os dados de um ciclo com visão sintética.

        - despesas_normais: transações de despesa SEM cartão de crédito
        - receitas: transações de receita
        - faturas_cartao: lista de faturas cujo due_day cai neste ciclo
        - cycle_day_1, cycle_day_2: limites dos ciclos
        - cycle_num: 1 ou 2
        """
        # Despesas agrupadas por categoria (SINTÉTICO)
        despesas_agrupadas = CycleService._group_expenses_by_category(despesas_normais)
        total_despesas_normais = float(sum((Decimal(str(d['total'])) for d in despesas_agrupadas), Decimal('0.00')))

        # Total das faturas de cartão que vencem neste ciclo
        if cycle_num == 1:
            faturas_do_ciclo = [f for f in faturas_cartao if f['due_day'] <= cycle_day_1]
        else:
            faturas_do_ciclo = [f for f in faturas_cartao if cycle_day_1 < f['due_day'] <= cycle_day_2]

        total_faturas = float(sum((Decimal(str(f['bill_total'])) for f in faturas_do_ciclo), Decimal('0.00')))

        # Total de receitas
        total_receitas = float(sum((t.amount for t in receitas), Decimal('0.00')))

        # Total geral de despesas = despesas normais + faturas de cartão
        total_despesas_geral = total_despesas_normais + total_faturas

        # Saldo do ciclo = receitas - despesas normais - faturas
        saldo = total_receitas - total_despesas_geral

        return {
            'receitas': receitas,
            'total_receitas': total_receitas,
            'despesas_agrupadas': despesas_agrupadas,  # SINTÉTICO por categoria
            'total_despesas_normais': total_despesas_normais,
            'faturas_cartao': faturas_do_ciclo,  # Faturas que vencem neste ciclo
            'total_faturas': total_faturas,
            'total_despesas': total_despesas_geral,  # Despesas normais + faturas
            'saldo': saldo,
        }

    @staticmethod
    def get_both_cycles(user_id: int, month: int, year: int):
        """
        Retorna os dados dos dois ciclos para o mês/ano informado com visão SINTÉTICA.

        MUDANÇA PRINCIPAL vs. versão anterior:
        - Transações de cartão de crédito são EXCLUÍDAS das despesas analíticas
        - Despesas normais são AGRUPADAS POR CATEGORIA (sintético)
        - Faturas de cartão aparecem como linha única por cartão, alocadas ao
          ciclo baseado no dia de VENCIMENTO (due_day) do cartão
        - Contas recorrentes são identificadas com seu vencimento
        """
        settings = CycleService.get_or_create_settings(user_id)
        cycle_day_1 = settings.cycle_day_1
        cycle_day_2 = settings.cycle_day_2

        # Busca todas as transações do mês/ano
        all_transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= date(year, month, 1),
            Transaction.date <= date(year, month, monthrange(year, month)[1])
        ).order_by(Transaction.date.asc()).all()

        # --- SEPARAÇÃO CRÍTICA ---
        # Remove transações de "Pagamento de Fatura" do fluxo de despesas
        # (elas são apenas transferências entre conta corrente e cartão)
        def is_bill_payment(t):
            return ('Pagamento' in t.description and 'Fatura' in t.description) or \
                   ('Pagamento' in t.description and 'Cartão' in t.description)

        # Transações que NÃO são de cartão de crédito e NÃO são pagamento de fatura
        transacoes_normais = [
            t for t in all_transactions
            if t.credit_card_id is None and not is_bill_payment(t)
        ]

        # Separa receitas e despesas NORMAIS (sem cartão) por ciclo
        receitas_1, despesas_1_normais = [], []
        receitas_2, despesas_2_normais = [], []

        for t in transacoes_normais:
            dia = t.date.day
            if t.type == 'RECEITA':
                if dia <= cycle_day_1:
                    receitas_1.append(t)
                else:
                    receitas_2.append(t)
            elif t.type == 'DESPESA':
                if dia <= cycle_day_1:
                    despesas_1_normais.append(t)
                else:
                    despesas_2_normais.append(t)

        # Busca faturas de cartão e contas recorrentes
        faturas_cartao = CycleService._get_credit_card_bills(user_id, month, year)
        contas_recorrentes = CycleService._get_recurring_bills_for_month(user_id, month, year)

        # Monta cada ciclo com visão sintética
        ciclo1 = CycleService._build_cycle(
            despesas_1_normais, receitas_1, faturas_cartao,
            cycle_day_1, cycle_day_2, cycle_num=1
        )
        ciclo2 = CycleService._build_cycle(
            despesas_2_normais, receitas_2, faturas_cartao,
            cycle_day_1, cycle_day_2, cycle_num=2
        )

        # Resumo geral do mês
        total_receitas_mes = ciclo1['total_receitas'] + ciclo2['total_receitas']
        total_despesas_mes = ciclo1['total_despesas'] + ciclo2['total_despesas']
        total_faturas_mes = ciclo1['total_faturas'] + ciclo2['total_faturas']

        return {
            'cycle_day_1': cycle_day_1,
            'cycle_day_2': cycle_day_2,
            'ciclo1': ciclo1,
            'ciclo2': ciclo2,
            'faturas_cartao': faturas_cartao,  # Todas as faturas do mês
            'contas_recorrentes': contas_recorrentes,  # Contas recorrentes do mês
            'total_receitas_mes': total_receitas_mes,
            'total_despesas_mes': total_despesas_mes,
            'total_faturas_mes': total_faturas_mes,
        }
