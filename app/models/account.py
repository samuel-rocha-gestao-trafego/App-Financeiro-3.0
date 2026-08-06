from datetime import datetime, timezone
from app.extensions import db


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    account_type = db.Column(db.String(40), nullable=False)  # Ex: Banco, Carteira, Dinheiro, Corrente, Investimento
    initial_balance = db.Column(db.Numeric(12, 2), default=0.00, nullable=False)
    current_balance = db.Column(db.Numeric(12, 2), default=0.00, nullable=False)
    color = db.Column(db.String(7), default='#0d6efd')  # Hex code
    icon = db.Column(db.String(50), default='bi-wallet2')  # Bootstrap Icon class
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic', cascade='all, delete-orphan')
    recurring_bills = db.relationship('RecurringBill', backref='account', lazy='dynamic')

    def __repr__(self):
        return f'<Account {self.name} (User {self.user_id})>'