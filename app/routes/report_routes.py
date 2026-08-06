from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from app.models.recurring_bill import RecurringBill
from app.models.account import Account
from app.models.transaction import Transaction
from app.services.recurring_service import RecurringService
from app.services.transaction_service import TransactionService
import csv
import io

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/recorrentes', methods=['GET', 'POST'])
@login_required
def recorrentes():
    """Gestão de recorrências — corrige bug P3 (agora suporta RECEITA)."""
    if request.method == 'POST':
        acao = request.form.get('acao')

        if acao == 'criar':
            try:
                descricao = request.form.get('descricao', '').strip()
                valor = float(request.form.get('valor', '0'))
                dia = int(request.form.get('dia_vencimento', '1'))
                periodicidade = request.form.get('periodicidade', 'Mensal')
                tipo = request.form.get('tipo', 'Despesa')
                conta_id = request.form.get('conta_id')

                trans_type = 'RECEITA' if tipo == 'Receita' else 'DESPESA'
                account_id = int(conta_id) if conta_id else None

                if not descricao or valor <= 0:
                    flash('Preencha descrição e valor.', 'danger')
                else:
                    RecurringService.create_recurring_bill(
                        user_id=current_user.id,
                        description=descricao,
                        amount=valor,
                        frequency=periodicidade,
                        due_day=dia,
                        trans_type=trans_type,
                        account_id=account_id
                    )
                    flash(f'Recorrência "{descricao}" cadastrada!', 'success')

            except Exception:
                flash('Erro ao criar recorrência.', 'danger')

        elif acao == 'excluir':
            recorrente_id = int(request.form.get('recorrente_id', 0))
            if RecurringService.delete_recurring_bill(recorrente_id, current_user.id):
                flash('Recorrência excluída!', 'success')
            else:
                flash('Recorrência não encontrada.', 'danger')

        return redirect(url_for('reports.recorrentes'))

    recorrentes_list = RecurringBill.query.filter_by(
        user_id=current_user.id, is_active=True
    ).order_by(RecurringBill.due_day.asc()).all()
    contas = Account.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'recorrentes.html',
        recorrentes=recorrentes_list,
        contas=contas
    )


@reports_bp.route('/processar-recorrente/<int:id>', methods=['POST'])
@login_required
def processar_recorrente(id):
    bill = RecurringBill.query.filter_by(id=id, user_id=current_user.id).first()
    if bill:
        RecurringService.generate_recurring_transactions(current_user.id)
        flash(f'Lançamento de "{bill.description}" processado!', 'success')
    else:
        flash('Recorrência não encontrada.', 'danger')
    return redirect(url_for('reports.recorrentes'))


@reports_bp.route('/exportar-csv')
@login_required
def exportar_csv():
    transactions = TransactionService.get_filtered(user_id=current_user.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Data', 'Tipo', 'Descrição', 'Valor', 'Status', 'Meio Pagamento', 'Conta'])

    for t in transactions:
        t_date = t.transaction_date or t.date
        writer.writerow([
            t.id,
            t_date.strftime('%Y-%m-%d') if t_date else '',
            t.type,
            t.description,
            t.amount,
            t.status,
            t.payment_method or '',
            t.account.name if t.account else ''
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment;filename=relatorio_financeiro.csv'
    return response
