from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import extract
from app.models.credit_card import CreditCard
from app.models.invoice import Invoice
from app.models.account import Account
from app.services.invoice_service import InvoiceService
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.credit_card_repository import CreditCardRepository

cards_bp = Blueprint('cards', __name__)


@cards_bp.route('/cartao', methods=['GET'])
@login_required
def dashboard_cartao():
    """Página de faturas — usa Invoice em vez de query direta (P1/P6)."""
    cartoes = CreditCardRepository.get_by_user(current_user.id)

    cartao_id = request.args.get('cartao_id', type=int)
    mes_atual = int(request.args.get('mes', datetime.utcnow().month))
    ano_atual = int(request.args.get('ano', datetime.utcnow().year))

    cartao_selecionado = None
    fatura = None
    fatura_items = []
    total_fatura = 0.0

    if cartoes:
        if not cartao_id or cartao_id not in [c.id for c in cartoes]:
            cartao_id = cartoes[0].id
        cartao_selecionado = CreditCardRepository.get_by_id_and_user(cartao_id, current_user.id)

        if cartao_selecionado:
            fatura = InvoiceRepository.get_by_card_month(cartao_id, mes_atual, ano_atual)
            if fatura:
                fatura_items = InvoiceRepository.get_transactions(fatura.id)
                total_fatura = float(fatura.total_amount)

    contas = Account.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'cartao.html',
        cartoes=cartoes,
        contas=contas,
        cartao_selecionado=cartao_selecionado,
        fatura=fatura,
        fatura_mes=fatura_items,
        total_fatura=total_fatura,
        mes_atual=mes_atual,
        ano_atual=ano_atual
    )


@cards_bp.route('/pagar-fatura', methods=['POST'])
@login_required
def pagar_fatura():
    """Paga fatura via InvoiceService (P6)."""
    invoice_id = int(request.form.get('invoice_id'))
    account_id = int(request.form.get('account_id'))
    cartao_id = int(request.form.get('cartao_id'))
    mes = int(request.form.get('mes'))
    ano = int(request.form.get('ano'))

    # Se não tem invoice_id, tentar buscar/create
    if not invoice_id:
        invoice = InvoiceRepository.get_by_card_month(cartao_id, mes, ano)
        if invoice:
            invoice_id = invoice.id
        else:
            flash('Fatura não encontrada para este mês.', 'danger')
            return redirect(url_for('cards.dashboard_cartao', cartao_id=cartao_id, mes=mes, ano=ano))

    if InvoiceService.pay_invoice(invoice_id, account_id, current_user.id):
        flash('Fatura paga com sucesso!', 'success')
    else:
        flash('Erro ao pagar fatura.', 'danger')

    return redirect(url_for('cards.dashboard_cartao', cartao_id=cartao_id, mes=mes, ano=ano))
