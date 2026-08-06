from datetime import datetime, timezone
from app.extensions import db


class Transaction(db.Model):
    """
    Modelo unificado de lançamento financeiro.

    Todas as movimentações (receitas, despesas, parcelas, recorrentes, cartão)
    passam por este modelo. A semântica é dada pelos campos:

    - transaction_date: data em que o evento financeiro ocorre (compra, vencimento)
    - due_date: data de vencimento/entrada prevista (para PENDENTE, igual ao transaction_date)
    - payment_date: data em que foi efetivamente pago/confirmado
    - competency_date: data de competência contábil (para relatórios)

    - payment_method: meio de pagamento (DINHEIRO, PIX, CARTAO_CREDITO, etc.)
    - invoice_id: se CARTAO_CREDITO, vincula à fatura correspondente
    - installment_group_id: se parcelado, vincula ao grupo de parcelas
    - installment_number: número desta parcela dentro do grupo (NULL se não parcelado)
    - is_recurring: se este lançamento foi gerado por regra de recorrência
    - recurring_parent_id: ID do lançamento que contém a regra de recorrência

    - status: PREVISTO ou REALIZADO (substitui o antigo PAGO/PENDENTE)
    """
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True, index=True)
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_cards.id', ondelete='SET NULL'), nullable=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True, index=True)
    installment_group_id = db.Column(db.Integer, db.ForeignKey('installment_groups.id', ondelete='SET NULL'), nullable=True, index=True)

    # Dados principais
    type = db.Column(db.String(20), nullable=False, index=True)  # 'RECEITA', 'DESPESA', 'TRANSFERENCIA'
    description = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    attachment_path = db.Column(db.String(255), nullable=True)

    # 4 datas semânticas
    transaction_date = db.Column(db.Date, nullable=False, index=True)  # Data do evento financeiro
    due_date = db.Column(db.Date, nullable=True, index=True)           # Vencimento previsto
    payment_date = db.Column(db.Date, nullable=True, index=True)      # Data do pagamento real
    competency_date = db.Column(db.Date, nullable=True, index=True)   # Competência (relatórios)

    # Meio de pagamento
    payment_method = db.Column(db.String(20), nullable=True, index=True)  # 'DINHEIRO','PIX','CARTAO_CREDITO',etc.

    # Status: PREVISTO ou REALIZADO
    status = db.Column(db.String(20), nullable=False, default='PREVISTO', index=True)

    # Parcelas
    installment_number = db.Column(db.Integer, nullable=True)  # Número da parcela (1..N), NULL se não parcelado

    # Recorrência
    is_recurring = db.Column(db.Boolean, default=False, nullable=False, index=True)
    recurring_parent_id = db.Column(db.Integer, db.ForeignKey('recurring_bills.id', ondelete='SET NULL'), nullable=True)  # FK para RecurringBill (template de recorrência)

    # Campo legacy para compatibilidade durante migração
    date = db.Column(db.Date, nullable=True)  # Manter temporariamente para templates antigos

    # Metadados
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def is_paid(self):
        return self.status == 'REALIZADO'

    @property
    def is_credit_card(self):
        return self.payment_method == 'CARTAO_CREDITO'

    @property
    def is_installment(self):
        return self.installment_group_id is not None

    @property
    def display_date(self):
        """Data para exibição: payment_date se pago, senão due_date ou transaction_date."""
        if self.payment_date:
            return self.payment_date
        if self.due_date:
            return self.due_date
        return self.transaction_date

    def __repr__(self):
        return f'<Transaction {self.description} - R${self.amount}>'
