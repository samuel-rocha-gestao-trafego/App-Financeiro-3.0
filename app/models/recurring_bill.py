from datetime import datetime, timezone
from app.extensions import db


class RecurringBill(db.Model):
    """
    Regra de recorrência de um lançamento financeiro.

    Ao contrário da arquitetura anterior onde RecurringBill gerava transações DESPESA
    por padrão (bug P3), agora suporta RECEITA e DESPESA.
    O campo 'type' define o tipo de transação gerada.
    """
    __tablename__ = 'recurring_bills'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_cards.id', ondelete='SET NULL'), nullable=True)

    description = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='DESPESA')  # 'RECEITA' ou 'DESPESA'
    frequency = db.Column(db.String(20), nullable=False)  # 'MENSAL', 'SEMANAL', 'ANUAL'
    due_day = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamento com as transações geradas
    generated_transactions = db.relationship('Transaction', backref='recurring_bill', lazy='dynamic',
                                             foreign_keys='Transaction.recurring_parent_id')

    def __repr__(self):
        return f'<RecurringBill {self.description} ({self.type}) - R${self.amount}>'
