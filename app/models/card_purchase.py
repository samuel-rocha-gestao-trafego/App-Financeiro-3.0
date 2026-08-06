from datetime import datetime, timezone
from app.extensions import db


class CardPurchase(db.Model):
    __tablename__ = 'card_purchases'

    id = db.Column(db.Integer, primary_key=True)
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_cards.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    
    description = db.Column(db.String(150), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    installments_count = db.Column(db.Integer, default=1, nullable=False)  # Número total de parcelas
    purchase_date = db.Column(db.Date, nullable=False)
    
    # Mês e ano da primeira fatura cobrada (Formato: YYYY e MM)
    first_bill_month = db.Column(db.Integer, nullable=False)
    first_bill_year = db.Column(db.Integer, nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<CardPurchase {self.description} ({self.installments_count}x)>'