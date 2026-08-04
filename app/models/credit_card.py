from datetime import datetime, timezone
from app.extensions import db


class CreditCard(db.Model):
    __tablename__ = 'credit_cards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    bank = db.Column(db.String(80), nullable=True)
    credit_limit = db.Column(db.Numeric(12, 2), default=0.00, nullable=True)
    closing_day = db.Column(db.Integer, default=10)
    due_day = db.Column(db.Integer, default=17)
    color = db.Column(db.String(7), default='#8b5cf6')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    purchases = db.relationship('CardPurchase', backref='credit_card', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='credit_card', lazy='dynamic')

    def __repr__(self):
        return f'<CreditCard {self.name}>'
