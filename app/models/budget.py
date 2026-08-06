from datetime import datetime, timezone
from app.extensions import db


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False, index=True)
    
    month = db.Column(db.Integer, nullable=False)  # 1 a 12
    year = db.Column(db.Integer, nullable=False)   # YYYY
    planned_amount = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category_id', 'month', 'year', name='uq_user_category_month_year'),
    )

    def __repr__(self):
        return f'<Budget Cat:{self.category_id} {self.month}/{self.year} - R${self.planned_amount}>'