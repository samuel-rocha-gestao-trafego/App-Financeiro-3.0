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

    from sqlalchemy import extract
    search = request.args.get('busca', '').strip()
    tipo = request.args.get('tipo', '').strip()
    forma = request.args.get('forma', '').strip()
    pago = request.args.get('pago', '').strip()
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)

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
    if mes:
        query = query.filter(extract('month', Transaction.date) == mes)
    if ano:
        query = query.filter(extract('year', Transaction.date) == ano)

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
            'pago': pago,
            'mes': mes,
            'ano': ano
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
            parcela_inicial = int(request.form.get('parcela_inicial', 1))
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
                # O índice 'i' representa o deslocamento em meses a partir da data da 1ª parcela
                current_parcela_num = i + 1
                
                # Se o usuário quer começar da parcela 9, pulamos as parcelas 1 a 8
                if current_parcela_num < parcela_inicial:
                    continue

                # A data da parcela atual é a data da 1ª parcela + 'i' meses
                parcela_data = trans_date
                parcela_desc = descricao
                parcela_valor = valor / parcelas

                if parcelas > 1:
                    parcela_desc = f"{descricao} ({current_parcela_num}/{parcelas})"
                    
                    # Calcula o mês e ano da parcela baseado no deslocamento 'i' desde a 1ª parcela
                    total_meses = parcela_data.month + i - 1
                    novo_mes = (total_meses % 12) + 1
                    novo_ano = parcela_data.year + (total_meses // 12)
                    
                    # Tenta manter o dia, mas ajusta se o mês for mais curto (ex: 31/01 -> 28/02)
                    dia = parcela_data.day
                    if dia > 28:
                        import calendar
                        ultimo_dia = calendar.monthrange(novo_ano, novo_mes)[1]
                        if dia > ultimo_dia:
                            dia = ultimo_dia
                            
                    parcela_data = parcela_data.replace(year=novo_ano, month=novo_mes, day=dia)

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
        
        db.session.commit()
        flash(f'{count} lançamentos excluídos com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir lançamentos em lote.', 'danger')

    return redirect(url_for('transactions.historico'))
