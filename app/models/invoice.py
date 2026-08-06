from datetime import datetime, timezone
from app.extensions import db


class Invoice(db.Model):
    """
    Fatura de cartão de crédito.

    Uma Invoice representa a fatura mensal de um cartão de crédito.
    As transações de cartão são vinculadas à fatura correspondente.
    O fluxo de vida: ABERTA -> FECHADA -> PAGA (ou ATRASADA).
    """
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_cards.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)   # YYYY

    closing_date = db.Column(db.Date, nullable=False)   # Data de fechamento da fatura
    due_date = db.Column(db.Date, nullable=False)       # Data de vencimento

    status = db.Column(db.String(20), nullable=False, default='ABERTA', index=True)
    # 'ABERTA', 'FECHADA', 'PAGA', 'ATRASADA'

    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    paid_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    paid_at = db.Column(db.DateTime, nullable=True)
    payment_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    transactions = db.relationship('Transaction', backref='invoice', lazy='dynamic',
                                  primaryjoin="Transaction.invoice_id == Invoice.id")
    credit_card = db.relationship('CreditCard', backref='invoices')
    payment_account = db.relationship('Account', foreign_keys=[payment_account_id])

    __table_args__ = (
        db.UniqueConstraint('credit_card_id', 'month', 'year', name='uq_card_month_year'),
    )

    @property
    def is_paid(self):
        return self.status == 'PAGA'

    @property
    def remaining(self):
        return self.total_amount - self.paid_amount

    def __repr__(self):
        return f'<Invoice {self.credit_card_id} {self.month:02d}/{self.year} - {self.status}>'
