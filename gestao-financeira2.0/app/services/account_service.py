from decimal import Decimal
from flask import flash
from app.extensions import db
from app.models.account import Account


class AccountService:

    @staticmethod
    def get_all_accounts(user_id: int, active_only: bool = False):
        """Retorna todas as contas do utilizador."""
        query = Account.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Account.name.asc()).all()

    @staticmethod
    def get_account_by_id(account_id: int, user_id: int):
        """Retorna uma conta específica pelo ID, validando o dono."""
        return Account.query.filter_by(id=account_id, user_id=user_id).first()

    @staticmethod
    def create_account(user_id: int, name: str, account_type: str, initial_balance: float, color: str, icon: str):
        """Cria uma nova conta bancária para o utilizador."""
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
            db.session.add(account)
            db.session.commit()
            return account
        except Exception:
            db.session.rollback()
            flash('Erro ao criar conta. Tente novamente.', 'danger')
            return None

    @staticmethod
    def delete_account(account_id: int, user_id: int):
        """Elimina uma conta do utilizador."""
        try:
            account = Account.query.filter_by(id=account_id, user_id=user_id).first()
            if account:
                db.session.delete(account)
                db.session.commit()
                return True
            return False
        except Exception:
            db.session.rollback()
            flash('Erro ao excluir conta. Tente novamente.', 'danger')
            return False

    @staticmethod
    def adjust_balance(account_id: int, amount_change):
        """Ajusta o saldo atual da conta (soma ou subtrai dependendo do sinal)."""
        account = Account.query.get(account_id)
        if account:
            account.current_balance += Decimal(str(amount_change))
            db.session.commit()

    @staticmethod
    def get_total_balance(user_id: int):
        """Retorna o saldo total de todas as contas ativas do utilizador."""
        accounts = Account.query.filter_by(user_id=user_id, is_active=True).all()
        return sum((acc.current_balance for acc in accounts), Decimal('0.00'))
