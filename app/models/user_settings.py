from datetime import datetime, timezone
from app.extensions import db


class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Dias de ciclo de pagamento (1-31)
    cycle_day_1 = db.Column(db.Integer, nullable=False, default=5)
    cycle_day_2 = db.Column(db.Integer, nullable=False, default=20)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<UserSettings user_id={self.user_id} ciclo1={self.cycle_day_1} ciclo2={self.cycle_day_2}>'
