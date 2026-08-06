from datetime import datetime
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import extract
from app.services.account_service import AccountService
from app.services.recurring_service import RecurringService
from app.services.cycle_service import CycleService
from app.models.transaction import Transaction
from app.models.credit_card import CreditCard

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def dashboard():
    # Processa pendências recorrentes do mês atual automaticamente
    RecurringService.generate_recurring_transactions(current_user.id)

    hoje = datetime.utcnow().date()

    # Filtro de mês/ano
    mes_atual = int(request.args.get('mes', hoje.month))
    ano_atual = int(request.args.get('ano', hoje.year))

    # Busca TODOS os lançamentos do mês
    todos_lancamentos = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.date) == mes_atual,
        extract('year', Transaction.date) == ano_atual
    ).order_by(Transaction.date.desc()).all()

    # --- SEPARAÇÃO: despesas normais vs cartão de crédito ---
    def is_bill_payment(t):
        return ('Pagamento' in t.description and 'Fatura' in t.description) or \
               ('Pagamento' in t.description and 'Cartão' in t.description)

    # Despesas NORMAIS (sem cartão de crédito e sem pagamento de fatura)
    despesas_normais = [
        t for t in todos_lancamentos
        if t.type == 'DESPESA' and t.credit_card_id is None and not is_bill_payment(t)
    ]
    receitas = [t for t in todos_lancamentos if t.type == 'RECEITA']

    # Cálculos CORRETOS: receitas e despesas do mês (excluindo cartão)
    receitas_val = float(sum((t.amount for t in receitas), 0))
    despesas_val = float(sum((t.amount for t in despesas_normais), 0))
    saldo_val = receitas_val - despesas_val

    contas_usuario = AccountService.get_all_accounts(current_user.id, active_only=True)
    saldo_total_val = float(sum((c.current_balance for c in contas_usuario), 0))

    # Últimos 5 lançamentos do mês (excluindo pagamentos de fatura para não confundir)
    ultimos = [
        t for t in todos_lancamentos
        if not is_bill_payment(t)
    ][:5]

    # Dados dos ciclos de pagamento (agora com visão sintética)
    ciclos = CycleService.get_both_cycles(current_user.id, mes_atual, ano_atual)

    # Cartões de crédito do usuário (para exibir resumo no dashboard)
    cartoes = CreditCard.query.filter_by(user_id=current_user.id).all()

    # Atualiza os totais do dashboard com dados sintéticos dos ciclos
    # (agora inclui faturas de cartão no total de despesas)
    total_despesas_completo = ciclos['total_despesas_mes']
    saldo_completo = ciclos['total_receitas_mes'] - total_despesas_completo

    return render_template(
        'dashboard.html',
        nome_utilizador=current_user.name or current_user.email,
        total_receitas=ciclos['total_receitas_mes'],
        total_despesas=total_despesas_completo,
        saldo=saldo_completo,
        saldo_total=saldo_total_val,
        mes_atual=mes_atual,
        ano_atual=ano_atual,
        contas=contas_usuario,
        ultimos_lancamentos=ultimos,
        ciclos=ciclos,
        cartoes=cartoes,
    )
