from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import extract
from app.extensions import db
from app.models.credit_card import CreditCard
from app.models.transaction import Transaction
from app.models.account import Account


cards_bp = Blueprint('cards', __name__)


@cards_bp.route('/cartao', methods=['GET'])
@login_required
def dashboard_cartao():
    """Página de consulta de fatura de cartão de crédito.
    
    MELHORIA: A fatura agora é calculada a partir das transações
    com credit_card_id, excluindo os lançamentos de pagamento de fatura.
    Mostra o dia de vencimento e fechamento do cartão integrado ao ciclo.
    """
    cartoes = CreditCard.query.filter_by(user_id=current_user.id).all()
    contas = Account.query.filter_by(user_id=current_user.id, is_active=True).all()

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
            # Busca transações do cartão no mês/ano (exclui pagamentos de fatura)
            todas_transacoes = Transaction.query.filter(
                Transaction.user_id == current_user.id,
                Transaction.credit_card_id == cartao_id,
                extract('month', Transaction.date) == mes_atual,
                extract('year', Transaction.date) == ano_atual
            ).all()

            # Filtra apenas os gastos reais (exclui "Pagamento Fatura ...")
            fatura_mes = [
                t for t in todas_transacoes
                if 'Pagamento' not in t.description and 'Fatura' not in t.description
            ]

            total_fatura = float(sum((t.amount for t in fatura_mes), Decimal('0')))

            # Verifica se já foi pago (lançamento de pagamento na conta corrente)
            fatura_paga = Transaction.query.filter(
                Transaction.user_id == current_user.id,
                Transaction.credit_card_id == cartao_id,
                extract('month', Transaction.date) == mes_atual,
                extract('year', Transaction.date) == ano_atual,
                Transaction.description.ilike("%Pagamento%Fatura%")
            ).first() is not None

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
    """Marca a fatura do cartão como paga, criando um lançamento de débito.
    
    MELHORIA: A data do pagamento usa o due_day do cartão (integrado ao ciclo)
    em vez de usar a data de hoje. Isso garante que o pagamento caia no dia
    correto dentro do ciclo de pagamento.
    """
    mes = int(request.form.get('mes'))
    ano = int(request.form.get('ano'))
    cartao_id = int(request.form.get('cartao_id'))
    account_id = int(request.form.get('account_id'))

    cartao = CreditCard.query.filter_by(id=cartao_id, user_id=current_user.id).first()
    if not cartao:
        flash('Cartão não encontrado.', 'danger')
        return redirect(url_for('cards.dashboard_cartao'))

    # Busca os gastos reais do cartão no mês (exclui pagamentos de fatura)
    todas_transacoes = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.credit_card_id == cartao_id,
        extract('month', Transaction.date) == mes,
        extract('year', Transaction.date) == ano
    ).all()

    gastos_reais = [
        t for t in todas_transacoes
        if 'Pagamento' not in t.description and 'Fatura' not in t.description
    ]

    total = Decimal(sum((t.amount for t in gastos_reais), Decimal('0')))

    if total <= 0:
        flash('Nenhum gasto para pagar nesta fatura.', 'warning')
        return redirect(url_for('cards.dashboard_cartao'))

    from app.services.transaction_service import TransactionService
    from calendar import monthrange

    # MELHORIA: Usa o due_day do cartão como data de pagamento
    # para integrar com o ciclo de pagamento corretamente
    last_day = monthrange(ano, mes)[1]
    dia_pagamento = min(cartao.due_day, last_day)
    data_pagamento = datetime(ano, mes, dia_pagamento).date()

    # Cria lançamento de pagamento da fatura
    TransactionService.create_transaction(
        user_id=current_user.id,
        account_id=account_id,
        category_id=None,
        trans_type='DESPESA',
        description=f"Pagamento Fatura {cartao.name} - {mes:02d}/{ano}",
        amount=float(total),
        trans_date=data_pagamento,
        status='PAGO',
        credit_card_id=cartao_id
    )

    flash(f'Fatura de R$ {total:.2f} do cartão {cartao.name} registrada como paga! Vencimento: dia {dia_pagamento}', 'success')
    return redirect(url_for('cards.dashboard_cartao', cartao_id=cartao_id, mes=mes, ano=ano))
