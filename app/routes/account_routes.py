from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.account import Account
from app.services.account_service import AccountService

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    """Página de configuração com gestão de contas e cartões."""
    if request.method == 'POST':
        acao = request.form.get('acao')

        try:
            if acao == 'nova_conta':
                nome = request.form.get('nome', '').strip()
                saldo = float(request.form.get('saldo_inicial', '0'))

                if not nome:
                    flash('O nome da conta é obrigatório.', 'danger')
                else:
                    AccountService.create_account(
                        user_id=current_user.id,
                        name=nome,
                        account_type='Carteira',
                        initial_balance=saldo,
                        color='#0d6efd',
                        icon='bi-bank'
                    )
                    flash(f'Conta "{nome}" criada com sucesso!', 'success')

            elif acao == 'excluir_conta':
                conta_id = int(request.form.get('conta_id', 0))
                if AccountService.delete_account(conta_id, current_user.id):
                    flash('Conta excluída com sucesso!', 'success')
                else:
                    flash('Conta não encontrada.', 'danger')

            elif acao == 'novo_cartao':
                from app.models.credit_card import CreditCard
                nome = request.form.get('nome', '').strip()
                dia_fechamento = int(request.form.get('dia_fechamento', 10))
                dia_vencimento = int(request.form.get('dia_vencimento', 17))
                limite = float(request.form.get('limite', '1000'))

                if not nome:
                    flash('O nome do cartão é obrigatório.', 'danger')
                else:
                    cartao = CreditCard(
                        user_id=current_user.id,
                        name=nome,
                        closing_day=dia_fechamento,
                        due_day=dia_vencimento,
                        credit_limit=Decimal(str(limite)),
                        color='#8b5cf6'
                    )
                    db.session.add(cartao)
                    db.session.commit()
                    flash(f'Cartão "{nome}" cadastrado com sucesso!', 'success')

            elif acao == 'excluir_cartao':
                from app.models.credit_card import CreditCard
                cartao_id = int(request.form.get('cartao_id', 0))
                cartao = CreditCard.query.filter_by(id=cartao_id, user_id=current_user.id).first()
                if cartao:
                    db.session.delete(cartao)
                    db.session.commit()
                    flash('Cartão excluído com sucesso!', 'success')
                else:
                    flash('Cartão não encontrado.', 'danger')

        except Exception:
            db.session.rollback()
            flash('Erro ao processar a ação. Tente novamente.', 'danger')

        return redirect(url_for('accounts.configuracoes'))

    contas = AccountService.get_all_accounts(current_user.id)
    cartoes = []
    try:
        from app.models.credit_card import CreditCard
        cartoes = CreditCard.query.filter_by(user_id=current_user.id).all()
    except Exception:
        pass

    return render_template(
        'configuracoes.html',
        contas=contas,
        cartoes=cartoes
    )
