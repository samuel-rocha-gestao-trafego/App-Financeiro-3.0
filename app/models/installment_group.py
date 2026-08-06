from datetime import datetime, timezone
from app.extensions import db


class InstallmentGroup(db.Model):
    """
    Agrupa parcelas de uma mesma compra.

    Quando um lançamento com parcelas > 1 é criado, geramos um InstallmentGroup
    e vinculamos cada parcela (Transaction) a este grupo via installment_group_id.
    """
    __tablename__ = 'installment_groups'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_cards.id', ondelete='SET NULL'), nullable=True, index=True)

    description = db.Column(db.String(150), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    installments_count = db.Column(db.Integer, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamento com as parcelas (transactions)
    transactions = db.relationship('Transaction', backref='installment_group', lazy='dynamic')

    def __repr__(self):
        return f'<InstallmentGroup {self.description} ({self.installments_count}x)>'
