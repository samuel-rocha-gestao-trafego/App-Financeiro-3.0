from datetime import datetime
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import extract
from app.services.account_service import AccountService
from app.services.recurring_service import RecurringService
from app.models.transaction import Transaction

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

    # Busca lançamentos filtrados pelo mês e ano
    lancamentos = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.date) == mes_atual,
        extract('year', Transaction.date) == ano_atual
    ).order_by(Transaction.date.desc()).all()

    contas_usuario = AccountService.get_all_accounts(current_user.id, active_only=True)

    # Cálculos de receitas e despesas do mês
    receitas_val = float(sum((t.amount for t in lancamentos if t.type == 'RECEITA'), 0))
    despesas_val = float(sum((t.amount for t in lancamentos if t.type == 'DESPESA'), 0))
    saldo_val = receitas_val - despesas_val

    # Saldo total real das contas (agregado)
    saldo_total_val = float(sum((c.current_balance for c in contas_usuario), 0))

    # Últimos 5 lançamentos do mês filtrado
    ultimos = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.date) == mes_atual,
        extract('year', Transaction.date) == ano_atual
    ).order_by(Transaction.date.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        nome_utilizador=current_user.name or current_user.email,
        total_receitas=receitas_val,
        total_despesas=despesas_val,
        saldo=saldo_val,
        saldo_total=saldo_total_val,
        mes_atual=mes_atual,
        ano_atual=ano_atual,
        contas=contas_usuario,
        ultimos_lancamentos=ultimos
    )
