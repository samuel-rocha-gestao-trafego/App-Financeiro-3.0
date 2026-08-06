from typing import List, Optional
from decimal import Decimal
from app.models.account import Account
from app.repositories.base_repository import BaseRepository


class AccountRepository(BaseRepository[Account]):
    model_class = Account

    @classmethod
    def get_active_by_user(cls, user_id: int) -> List[Account]:
        return Account.query.filter_by(user_id=user_id, is_active=True).order_by(Account.name.asc()).all()

    @classmethod
    def get_total_balance(cls, user_id: int) -> Decimal:
        """Retorna saldo total de todas as contas ativas."""
        accounts = Account.query.filter_by(user_id=user_id, is_active=True).all()
        return sum((acc.current_balance for acc in accounts), Decimal('0.00'))

    @classmethod
    def adjust_balance(cls, account_id: int, amount_change) -> bool:
        """Ajusta o saldo atual da conta."""
        account = Account.query.get(account_id)
        if account:
            account.current_balance += Decimal(str(amount_change))
            db.session.commit()
            return True
        return False
