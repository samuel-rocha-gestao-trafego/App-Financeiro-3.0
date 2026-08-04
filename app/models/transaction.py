from datetime import datetime, timezone
from app.extensions import db


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=True, index=True)
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_cards.id', ondelete='SET NULL'), nullable=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Campo opcional para vincular movimentação a uma conta recorrente
    recurring_bill_id = db.Column(db.Integer, db.ForeignKey('recurring_bills.id', ondelete='SET NULL'), nullable=True)

    type = db.Column(db.String(20), nullable=False, index=True)  # 'RECEITA', 'DESPESA', 'TRANSFERENCIA'
    description = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), default='PAGO', nullable=False)  # 'PAGO', 'PENDENTE'
    notes = db.Column(db.Text, nullable=True)
    attachment_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Transaction {self.description} - R${self.amount}>'
