from decimal import Decimal
from flask import flash
from app.extensions import db
from app.models.account import Account
from app.repositories.account_repository import AccountRepository


class AccountService:
    """Serviço de gestão de contas bancárias."""

    @staticmethod
    def get_all_accounts(user_id: int, active_only: bool = False):
        if active_only:
            return AccountRepository.get_active_by_user(user_id)
        return AccountRepository.get_by_user(user_id)

    @staticmethod
    def get_account_by_id(account_id: int, user_id: int):
        return Account.query.filter_by(id=account_id, user_id=user_id).first()

    @staticmethod
    def create_account(user_id: int, name: str, account_type: str, initial_balance: float, color: str = '#0d6efd', icon: str = 'bi-wallet2'):
        try:
            balance_decimal = Decimal(str(initial_balance or 0.0))
            account = Account(
                user_id=user_id,
                name=name,
                account_type=account_type,
                initial_balance=balance_decimal,
                current_balance=balance_decimal,
                color=color,
                icon=icon
            )
            return AccountRepository.save(account)
        except Exception:
            db.session.rollback()
            flash('Erro ao criar conta. Tente novamente.', 'danger')
            return None

    @staticmethod
    def delete_account(account_id: int, user_id: int):
        account = AccountService.get_account_by_id(account_id, user_id)
        if account:
            return AccountRepository.delete(account)
        return False

    @staticmethod
    def get_total_balance(user_id: int):
        return AccountRepository.get_total_balance(user_id)
