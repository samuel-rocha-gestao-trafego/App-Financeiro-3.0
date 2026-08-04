from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import extract
from app.extensions import db
from app.models.credit_card import CreditCard
from app.models.transaction import Transaction

cards_bp = Blueprint('cards', __name__)


@cards_bp.route('/cartao', methods=['GET'])
@login_required
def dashboard_cartao():
    """Página de consulta de fatura de cartão de crédito."""
    cartoes = CreditCard.query.filter_by(user_id=current_user.id).all()

    cartao_id = request.args.get('cartao_id', type=int)
    mes_atual = int(request.args.get('mes', datetime.utcnow().month))
    ano_atual = int(request.args.get('ano', datetime.utcnow().year))

    cartao_selecionado = None
    fatura_mes = []
    total_fatura = 0.0
    fatura_paga = False

    if cartoes:
        if not cartao_id or cartao_id not in [c.id for c in cartoes]:
            cartao_id = cartoes[0].id
        cartao_selecionado = CreditCard.query.get(cartao_id)

        if cartao_selecionado:
            fatura_mes = Transaction.query.filter(
                Transaction.user_id == current_user.id,
                Transaction.credit_card_id == cartao_id,
                extract('month', Transaction.date) == mes_atual,
                extract('year', Transaction.date) == ano_atual
            ).all()

            total_fatura = float(sum((t.amount for t in fatura_mes), Decimal('0')))

            # Verifica se já foi pago (lançamento de pagamento)
            fatura_paga = Transaction.query.filter(
                Transaction.user_id == current_user.id,
                Transaction.credit_card_id == cartao_id,
                extract('month', Transaction.date) == mes_atual,
                extract('year', Transaction.date) == ano_atual,
                Transaction.description.ilike("%Pagamento%Cartão%")
            ).first() is not None

    from app.models.account import Account
    contas = Account.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'cartao.html',
        cartoes=cartoes,
        contas=contas,
        cartao_selecionado=cartao_selecionado,
        fatura_mes=fatura_mes,
        total_fatura=total_fatura,
        fatura_paga=fatura_paga,
        mes_atual=mes_atual,
        ano_atual=ano_atual
    )


@cards_bp.route('/pagar-fatura', methods=['POST'])
@login_required
def pagar_fatura():
    """Marca a fatura do cartão como paga, criando um lançamento de débito."""
    mes = int(request.form.get('mes'))
    ano = int(request.form.get('ano'))
    cartao_id = int(request.form.get('cartao_id'))
    account_id = int(request.form.get('account_id'))

    cartao = CreditCard.query.filter_by(id=cartao_id, user_id=current_user.id).first()
    if not cartao:
        flash('Cartão não encontrado.', 'danger')
        return redirect(url_for('cards.dashboard_cartao'))

    # Calcula total da fatura
    gastos_mes = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.credit_card_id == cartao_id,
        extract('month', Transaction.date) == mes,
        extract('year', Transaction.date) == ano
    ).all()

    total = Decimal(sum((t.amount for t in gastos_mes), Decimal('0')))

    if total <= 0:
        flash('Nenhum gasto para pagar nesta fatura.', 'warning')
        return redirect(url_for('cards.dashboard_cartao'))

    from app.services.transaction_service import TransactionService
    
    # Cria lançamento de pagamento da fatura usando o serviço para ajustar o saldo
    TransactionService.create_transaction(
        user_id=current_user.id,
        account_id=account_id,
        category_id=None,
        trans_type='DESPESA',
        description=f"Pagamento Fatura {cartao.name} - {mes:02d}/{ano}",
        amount=float(total),
        trans_date=datetime.utcnow().date(),
        status='PAGO',
        credit_card_id=cartao_id
    )

    flash(f'Fatura de R$ {total:.2f} do cartão {cartao.name} registrada como paga!', 'success')
    return redirect(url_for('cards.dashboard_cartao', cartao_id=cartao_id, mes=mes, ano=ano))
