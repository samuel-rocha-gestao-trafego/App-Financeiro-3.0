from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import extract
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.credit_card import CreditCard
from app.services.transaction_service import TransactionService
from app.models.enums import PaymentMethod

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/lancamentos', methods=['GET'])
@login_required
def historico():
    """Lista histórica com filtros — lógica delegada ao service/repo."""
    contas = Account.query.filter_by(user_id=current_user.id).all()
    cartoes = CreditCard.query.filter_by(user_id=current_user.id).all()

    search = request.args.get('busca', '').strip()
    tipo = request.args.get('tipo', '').strip()
    forma = request.args.get('forma', '').strip()
    status = request.args.get('status', '').strip()
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)

    # Mapear forma de pagamento para payment_method
    payment_method = None
    if forma == 'Cartão de Crédito':
        payment_method = 'CARTAO_CREDITO'
    elif forma == 'Pix / Dinheiro':
        payment_method = 'PIX'
    elif forma == 'Débito':
        payment_method = 'DEBITO'

    # Construir filtros para o repositório
    filters = {}
    if search:
        filters['search'] = search
    if tipo:
        filters['trans_type'] = tipo
    if payment_method:
        filters['payment_method'] = payment_method
    if status:
        filters['status'] = status
    if mes:
        filters['month_filter'] = mes
    if ano:
        filters['year_filter'] = ano

    # Usar transaction_date para filtros de mês/ano
    lancamentos = TransactionService.get_filtered(current_user.id, **filters)

    # Se tem filtro de mês/ano, aplicar via query direta
    if mes or ano:
        query = Transaction.query.filter_by(user_id=current_user.id)
        if tipo:
            query = query.filter_by(type=tipo)
        if payment_method:
            query = query.filter_by(payment_method=payment_method)
        if status:
            query = query.filter_by(status=status)
        if search:
            query = query.filter(Transaction.description.ilike(f'%{search}%'))
        if mes:
            query = query.filter(extract('month', Transaction.transaction_date) == mes)
        if ano:
            query = query.filter(extract('year', Transaction.transaction_date) == ano)
        lancamentos = query.order_by(Transaction.transaction_date.desc()).all()

    return render_template(
        'historico.html',
        lancamentos=lancamentos,
        contas=contas,
        cartoes=cartoes,
        filtros={
            'busca': search,
            'tipo': tipo,
            'forma': forma,
            'status': status,
            'mes': mes,
            'ano': ano
        }
    )


@transactions_bp.route('/novo-lancamento', methods=['GET', 'POST'])
@login_required
def novo_lancamento():
    """Cria lançamento — lógica de parcelamento delegada ao service (P4)."""
    contas = Account.query.filter_by(user_id=current_user.id, is_active=True).all()
    cartoes = CreditCard.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        try:
            descricao = request.form.get('descricao', '').strip()
            valor = float(request.form.get('valor', '0'))
            tipo = request.form.get('tipo', 'Despesa')
            forma_pagamento = request.form.get('forma_pagamento', 'Pix / Dinheiro')
            conta_id = request.form.get('conta_id')
            cartao_id = request.form.get('cartao_id')
            data_str = request.form.get('data', '')
            parcelas = int(request.form.get('parcelas', 1))
            pago = request.form.get('pago') == 'on'

            if not descricao or valor <= 0:
                flash('Preencha a descrição e o valor.', 'danger')
                return redirect(url_for('transactions.novo_lancamento'))

            trans_type = 'RECEITA' if tipo == 'Receita' else 'DESPESA'
            status = 'REALIZADO' if pago else 'PREVISTO'
            payment_method = PaymentMethod.from_form(forma_pagamento).value

            try:
                trans_date = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data inválida.', 'danger')
                return redirect(url_for('transactions.novo_lancamento'))

            account_id = int(conta_id) if conta_id else None
            card_id = int(cartao_id) if (cartao_id and payment_method == 'CARTAO_CREDITO') else None

            if parcelas > 1:
                # Delegar parcelamento ao service (P4)
                TransactionService.create_with_installments(
                    user_id=current_user.id,
                    trans_type=trans_type,
                    description=descricao,
                    total_amount=valor,
                    installments_count=parcelas,
                    first_installment_date=trans_date,
                    account_id=account_id,
                    credit_card_id=card_id,
                    payment_method=payment_method,
                    status=status,
                )
            else:
                TransactionService.create_transaction(
                    user_id=current_user.id,
                    trans_type=trans_type,
                    description=descricao,
                    amount=valor,
                    transaction_date=trans_date,
                    account_id=account_id,
                    credit_card_id=card_id,
                    payment_method=payment_method,
                    status=status,
                )

            flash('Lançamento criado com sucesso!', 'success')
            return redirect(url_for('transactions.historico'))

        except Exception:
            flash('Erro ao criar lançamento. Tente novamente.', 'danger')

    return render_template(
        'lancamentos.html',
        contas=contas,
        cartoes=cartoes
    )


@transactions_bp.route('/lancamento/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_lancamento(id):
    """Edita lançamento existente."""
    lancamento = Transaction.query.get_or_404(id)
    if lancamento.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('transactions.historico'))

    contas = Account.query.filter_by(user_id=current_user.id).all()
    cartoes = CreditCard.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        try:
            lancamento.description = request.form.get('descricao', '').strip()
            lancamento.amount = float(request.form.get('valor', '0'))
            lancamento.type = 'RECEITA' if request.form.get('tipo') == 'Receita' else 'DESPESA'

            pago = request.form.get('pago') == 'on'
            lancamento.status = 'REALIZADO' if pago else 'PREVISTO'

            data_str = request.form.get('data', '')
            if data_str:
                new_date = datetime.strptime(data_str, '%Y-%m-%d').date()
                lancamento.transaction_date = new_date
                lancamento.due_date = new_date
                if pago:
                    lancamento.payment_date = new_date
                lancamento.date = new_date  # Legacy compat

            conta_id = request.form.get('conta_id')
            lancamento.account_id = int(conta_id) if conta_id else None

            from app.extensions import db
            db.session.commit()
            flash('Lançamento atualizado com sucesso!', 'success')
            return redirect(url_for('transactions.historico'))

        except Exception:
            db.session.rollback()
            flash('Erro ao atualizar lançamento.', 'danger')

    return render_template(
        'editar_lancamento.html',
        l=lancamento,
        contas=contas,
        cartoes=cartoes
    )


@transactions_bp.route('/lancamento/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_lancamento(id):
    """Exclui um lançamento financeiro."""
    lancamento = Transaction.query.get_or_404(id)
    if lancamento.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('transactions.historico'))

    TransactionService.delete_transaction(lancamento)
    flash('Lançamento excluído com sucesso!', 'success')
    return redirect(url_for('transactions.historico'))


@transactions_bp.route('/lancamentos/excluir-lote', methods=['POST'])
@login_required
def excluir_lote():
    """Exclui múltiplos lançamentos de uma vez."""
    transaction_ids = request.form.getlist('ids[]')
    if not transaction_ids:
        flash('Nenhum lançamento selecionado.', 'warning')
        return redirect(url_for('transactions.historico'))

    try:
        count = 0
        for tid in transaction_ids:
            lancamento = Transaction.query.get(int(tid))
            if lancamento and lancamento.user_id == current_user.id:
                TransactionService.delete_transaction(lancamento)
                count += 1
        flash(f'{count} lançamentos excluídos com sucesso!', 'success')
    except Exception:
        flash('Erro ao excluir lançamentos em lote.', 'danger')

    return redirect(url_for('transactions.historico'))


@transactions_bp.route('/lancamento/realizar/<int:id>', methods=['POST'])
@login_required
def realizar_lancamento(id):
    """Marca um lançamento PREVISTO como REALIZADO."""
    lancamento = Transaction.query.get_or_404(id)
    if lancamento.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('transactions.historico'))

    if TransactionService.mark_as_realized(lancamento):
        flash('Lançamento marcado como realizado!', 'success')
    else:
        flash('Erro ao atualizar lançamento.', 'danger')

    return redirect(url_for('transactions.historico'))
