from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from app.extensions import db
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
    """Página de gestão de contas recorrentes."""
    if request.method == 'POST':
        acao = request.form.get('acao')

        if acao == 'criar':
            try:
                descricao = request.form.get('descricao', '').strip()
                valor = float(request.form.get('valor', '0'))
                dia = int(request.form.get('dia_vencimento', '1'))
                periodicidade = request.form.get('periodicidade', 'Mensal')
                conta_id = request.form.get('conta_id')

                account_id = int(conta_id) if conta_id else None

                if not descricao or valor <= 0:
                    flash('Preencha a descrição e o valor corretamente.', 'danger')
                else:
                    RecurringService.create_recurring_bill(
                        user_id=current_user.id,
                        description=descricao,
                        amount=valor,
                        frequency=periodicidade,
                        due_day=dia,
                        category_id=None,
                        account_id=account_id
                    )
                    flash(f'Recorrência "{descricao}" cadastrada!', 'success')

            except Exception:
                db.session.rollback()
                flash('Erro ao criar recorrência.', 'danger')

        elif acao == 'excluir':
            recorrente_id = int(request.form.get('recorrente_id', 0))
            if RecurringService.delete_recurring_bill(recorrente_id, current_user.id):
                flash('Recorrência excluída com sucesso!', 'success')
            else:
                flash('Recorrência não encontrada.', 'danger')

        return redirect(url_for('reports.recorrentes'))

    recorrentes_list = RecurringBill.query.filter_by(user_id=current_user.id, is_active=True).order_by(RecurringBill.due_day.asc()).all()
    contas = Account.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'recorrentes.html',
        recorrentes=recorrentes_list,
        contas=contas
    )


@reports_bp.route('/processar-recorrente/<int:id>', methods=['POST'])
@login_required
def processar_recorrente(id):
    """Processa imediatamente um lançamento recorrente."""
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
    """Exporta lançamentos em formato CSV."""
    transactions = TransactionService.get_filtered_transactions(user_id=current_user.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Data', 'Tipo', 'Descrição', 'Valor', 'Status', 'Conta'])

    for t in transactions:
        writer.writerow([
            t.id,
            t.date.strftime('%Y-%m-%d'),
            t.type,
            t.description,
            t.amount,
            t.status,
            t.account.name if t.account else ''
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment;filename=relatorio_financeiro.csv'
    return response
