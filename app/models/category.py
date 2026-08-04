from datetime import datetime, timezone
from app.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'RECEITA' ou 'DESPESA'
    color = db.Column(db.String(7), default='#6c757d')
    icon = db.Column(db.String(50), default='bi-tag')
    monthly_limit = db.Column(db.Numeric(12, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')
    budgets = db.relationship('Budget', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    recurring_bills = db.relationship('RecurringBill', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name} ({self.type})>'