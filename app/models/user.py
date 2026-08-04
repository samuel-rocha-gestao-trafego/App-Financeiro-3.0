from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    accounts = db.relationship('Account', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    credit_cards = db.relationship('CreditCard', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    recurring_bills = db.relationship('RecurringBill', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'
