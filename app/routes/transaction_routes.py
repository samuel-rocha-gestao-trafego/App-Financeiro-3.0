from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.credit_card import CreditCard
from app.services.transaction_service import TransactionService

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/lancamentos', methods=['GET'])
@login_required
def historico():
    """Lista histórica de lançamentos com filtros."""
    contas = Account.query.filter_by(user_id=current_user.id).all()
    cartoes = CreditCard.query.filter_by(user_id=current_user.id).all()

    search = request.args.get('busca', '').strip()
    tipo = request.args.get('tipo', '').strip()
    forma = request.args.get('forma', '').strip()
    pago = request.args.get('pago', '').strip()

    query = Transaction.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))
    if tipo:
        query = query.filter_by(type=tipo)
    if forma == 'Cartão de Crédito':
        query = query.filter(Transaction.credit_card_id.isnot(None))
    elif forma == 'Conta':
        query = query.filter(Transaction.account_id.isnot(None))
    if pago:
        query = query.filter_by(status=pago)

    lancamentos = query.order_by(Transaction.date.desc()).all()

    return render_template(
        'historico.html',
        lancamentos=lancamentos,
        contas=contas,
        cartoes=cartoes,
        filtros={
            'busca': search,
            'tipo': tipo,
            'forma': forma,
            'pago': pago
        }
    )


@transactions_bp.route('/novo-lancamento', methods=['GET', 'POST'])
@login_required
def novo_lancamento():
    """Cria um novo lançamento financeiro."""
    contas = Account.query.filter_by(user_id=current_user.id, is_active=True).all()
    cartoes = CreditCard.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        try:
            descricao = request.form.get('descricao', '').strip()
            valor = float(request.form.get('valor', '0'))
            tipo = request.form.get('tipo', 'Despesa')
            categoria = request.form.get('categoria', 'Geral')
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
            status = 'PAGO' if pago else 'PENDENTE'

            # Converte data string para date
            try:
                trans_date = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Data inválida.', 'danger')
                return redirect(url_for('transactions.novo_lancamento'))

            account_id = int(conta_id) if conta_id else None
            card_id = int(cartao_id) if (cartao_id and forma_pagamento == 'Cartão de Crédito') else None

            for i in range(parcelas):
                parcela_data = trans_date
                parcela_desc = descricao
                parcela_valor = valor / parcelas

                if parcelas > 1:
                    parcela_desc = f"{descricao} ({i+1}/{parcelas})"
                    # Avança o mês para cada parcela
                    mes = parcela_data.month + i
                    ano = parcela_data.year
                    while mes > 12:
                        mes -= 12
                        ano += 1
                    parcela_data = parcela_data.replace(year=ano, month=mes)

                TransactionService.create_transaction(
                    user_id=current_user.id,
                    account_id=account_id,
                    category_id=None,
                    trans_type=trans_type,
                    description=parcela_desc,
                    amount=parcela_valor,
                    trans_date=parcela_data,
                    status=status,
                    credit_card_id=card_id
                )

            flash('Lançamento criado com sucesso!', 'success')
            return redirect(url_for('transactions.historico'))

        except Exception:
            db.session.rollback()
            flash('Erro ao criar lançamento. Tente novamente.', 'danger')

    return render_template(
        'lancamentos.html',
        contas=contas,
        cartoes=cartoes
    )


@transactions_bp.route('/lancamento/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_lancamento(id):
    """Edita um lançamento existente."""
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
            lancamento.status = 'PAGO' if request.form.get('pago') else 'PENDENTE'

            data_str = request.form.get('data', '')
            if data_str:
                lancamento.date = datetime.strptime(data_str, '%Y-%m-%d').date()

            conta_id = request.form.get('conta_id')
            lancamento.account_id = int(conta_id) if conta_id else None
            
            cartao_id = request.form.get('cartao_id')
            lancamento.credit_card_id = int(cartao_id) if cartao_id else None

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

    try:
        TransactionService.delete_transaction(lancamento)
        flash('Lançamento excluído com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao excluir lançamento.', 'danger')

    return redirect(url_for('transactions.historico'))
