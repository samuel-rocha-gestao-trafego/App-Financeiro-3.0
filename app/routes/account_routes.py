from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.account import Account
from app.services.account_service import AccountService
from app.services.cycle_service import CycleService

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    """Página de configuração com gestão de contas, cartões e ciclos de pagamento."""
    if request.method == 'POST':
        acao = request.form.get('acao')

        try:
            if acao == 'salvar_ciclos':
                ciclo1 = int(request.form.get('ciclo_dia_1', 5))
                ciclo2 = int(request.form.get('ciclo_dia_2', 20))

                if ciclo1 < 1 or ciclo1 > 31 or ciclo2 < 1 or ciclo2 > 31:
                    flash('Os dias dos ciclos devem estar entre 1 e 31.', 'danger')
                elif ciclo1 >= ciclo2:
                    flash('O 1º ciclo deve ser menor que o 2º ciclo.', 'danger')
                else:
                    if CycleService.update_cycle_settings(current_user.id, ciclo1, ciclo2):
                        flash('Ciclos de pagamento atualizados com sucesso!', 'success')
                    else:
                        flash('Erro ao salvar ciclos. Tente novamente.', 'danger')

            elif acao == 'nova_conta':
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

    # Buscar configurações de ciclo do usuário
    cycle_settings = CycleService.get_or_create_settings(current_user.id)

    return render_template(
        'configuracoes.html',
        contas=contas,
        cartoes=cartoes,
        cycle_settings=cycle_settings
    )
