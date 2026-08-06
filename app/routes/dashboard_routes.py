from datetime import datetime
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import extract
from app.models.transaction import Transaction
from app.services.account_service import AccountService
from app.services.recurring_service import RecurringService
from app.services.cycle_service import CycleService
from app.services.report_service import ReportService

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def dashboard():
    # Processa recorrências do mês
    RecurringService.generate_recurring_transactions(current_user.id)

    hoje = datetime.utcnow().date()
    mes_atual = int(request.args.get('mes', hoje.month))
    ano_atual = int(request.args.get('ano', hoje.year))

    # Busca lançamentos do mês usando transaction_date
    lancamentos = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.transaction_date) == mes_atual,
        extract('year', Transaction.transaction_date) == ano_atual
    ).order_by(Transaction.transaction_date.desc()).all()

    contas_usuario = AccountService.get_all_accounts(current_user.id, active_only=True)

    # Resumo do mês (realizado)
    receitas_val = float(sum((t.amount for t in lancamentos if t.type == 'RECEITA' and t.status == 'REALIZADO'), 0))
    despesas_val = float(sum((t.amount for t in lancamentos if t.type == 'DESPESA' and t.status == 'REALIZADO'), 0))
    saldo_val = receitas_val - despesas_val

    # Previstos
    prev_receitas = float(sum((t.amount for t in lancamentos if t.type == 'RECEITA'), 0))
    prev_despesas = float(sum((t.amount for t in lancamentos if t.type == 'DESPESA'), 0))
    prev_saldo = prev_receitas - prev_despesas

    # Saldo total real
    saldo_total_val = float(AccountService.get_total_balance(current_user.id))

    # Últimos 5
    ultimos = lancamentos[:5]

    # Ciclos
    ciclos = CycleService.get_both_cycles(current_user.id, mes_atual, ano_atual)

    # Cash flow previsto vs realizado
    cash_flow = ReportService.get_cash_flow(current_user.id, mes_atual, ano_atual)

    return render_template(
        'dashboard.html',
        nome_utilizador=current_user.name or current_user.email,
        total_receitas=receitas_val,
        total_despesas=despesas_val,
        saldo=saldo_val,
        prev_receitas=prev_receitas,
        prev_despesas=prev_despesas,
        prev_saldo=prev_saldo,
        saldo_total=saldo_total_val,
        mes_atual=mes_atual,
        ano_atual=ano_atual,
        contas=contas_usuario,
        ultimos_lancamentos=ultimos,
        ciclos=ciclos,
        cash_flow=cash_flow,
    )
