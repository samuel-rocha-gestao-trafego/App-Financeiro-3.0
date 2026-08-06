from datetime import date, timedelta
from decimal import Decimal
from calendar import monthrange
from flask import flash
from app.extensions import db
from app.models.transaction import Transaction
from app.models.installment_group import InstallmentGroup
from app.models.enums import PaymentMethod, EntryStatus
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.account_repository import AccountRepository


class TransactionService:
    """
    Serviço principal de transações.

    Responsabilidades:
    - Criar transações únicas ou parceladas
    - Ajustar saldo da conta quando realizado
    - Vincular à Invoice quando cartão de crédito
    - Excluir e reverter impactos
    """

    @staticmethod
    def create_transaction(
        user_id: int,
        trans_type: str,
        description: str,
        amount: float,
        transaction_date: date,
        account_id: int = None,
        category_id: int = None,
        credit_card_id: int = None,
        payment_method: str = None,
        status: str = 'PREVISTO',
        notes: str = None,
        due_date: date = None,
        invoice_id: int = None,
        installment_group_id: int = None,
        installment_number: int = None,
        is_recurring: bool = False,
        recurring_parent_id: int = None,
    ) -> Transaction:
        """Cria uma transação e ajusta saldo se REALIZADO."""
        try:
            amount_decimal = Decimal(str(amount))

            transaction = Transaction(
                user_id=user_id,
                account_id=account_id,
                category_id=category_id,
                credit_card_id=credit_card_id,
                type=trans_type,
                description=description,
                amount=amount_decimal,
                transaction_date=transaction_date,
                due_date=due_date or transaction_date,
                payment_date=transaction_date if status == 'REALIZADO' else None,
                competency_date=transaction_date,
                payment_method=payment_method,
                status=status,
                notes=notes,
                invoice_id=invoice_id,
                installment_group_id=installment_group_id,
                installment_number=installment_number,
                is_recurring=is_recurring,
                recurring_parent_id=recurring_parent_id,
                # Compatibilidade legacy
                date=transaction_date,
            )
            db.session.add(transaction)
            db.session.flush()

            # Se realizado e não é cartão de crédito, ajusta saldo da conta
            if status == 'REALIZADO' and payment_method != 'CARTAO_CREDITO' and account_id:
                if trans_type == 'RECEITA':
                    AccountRepository.adjust_balance(account_id, amount_decimal)
                elif trans_type == 'DESPESA':
                    AccountRepository.adjust_balance(account_id, -amount_decimal)

            db.session.commit()
            return transaction
        except Exception:
            db.session.rollback()
            flash('Erro ao criar lançamento. Tente novamente.', 'danger')
            return None

    @staticmethod
    def create_with_installments(
        user_id: int,
        trans_type: str,
        description: str,
        total_amount: float,
        installments_count: int,
        first_installment_date: date,
        account_id: int = None,
        category_id: int = None,
        credit_card_id: int = None,
        payment_method: str = None,
        status: str = 'PREVISTO',
    ) -> list:
        """
        Cria um grupo de parcelas.

        Retorna lista de Transactions criadas.
        Move lógica de parcelamento do controller para o service (P4).
        """
        try:
            total_decimal = Decimal(str(total_amount))
            installment_value = total_decimal / Decimal(installments_count)

            # Criar grupo de parcelas
            group = InstallmentGroup(
                user_id=user_id,
                credit_card_id=credit_card_id,
                description=description,
                total_amount=total_decimal,
                installments_count=installments_count,
                purchase_date=first_installment_date
            )
            db.session.add(group)
            db.session.flush()

            transactions = []
            for i in range(installments_count):
                current_num = i + 1

                # Calcular data da parcela
                total_months = first_installment_date.month + i
                novo_mes = (total_months - 1) % 12 + 1
                novo_ano = first_installment_date.year + ((total_months - 1) // 12)
                dia = min(first_installment_date.day, monthrange(novo_ano, novo_mes)[1])
                parcela_date = date(novo_ano, novo_mes, dia)

                # Vincular à Invoice se for cartão de crédito
                invoice_id = None
                if payment_method == 'CARTAO_CREDITO' and credit_card_id:
                    from app.services.invoice_service import InvoiceService
                    invoice = InvoiceService.get_or_create_invoice(credit_card_id, user_id, novo_mes, novo_ano)
                    invoice_id = invoice.id if invoice else None

                desc = f'{description} ({current_num}/{installments_count})'

                t = TransactionService.create_transaction(
                    user_id=user_id,
                    trans_type=trans_type,
                    description=desc,
                    amount=float(installment_value),
                    transaction_date=parcela_date,
                    account_id=account_id,
                    category_id=category_id,
                    credit_card_id=credit_card_id,
                    payment_method=payment_method,
                    status=status,
                    invoice_id=invoice_id,
                    installment_group_id=group.id,
                    installment_number=current_num,
                )
                if t:
                    transactions.append(t)

            return transactions
        except Exception:
            db.session.rollback()
            flash('Erro ao criar parcelas. Tente novamente.', 'danger')
            return []

    @staticmethod
    def delete_transaction(transaction: Transaction):
        """Exclui transação e reverte impacto no saldo se REALIZADO."""
        try:
            if transaction.status == 'REALIZADO' and transaction.payment_method != 'CARTAO_CREDITO' and transaction.account_id:
                if transaction.type == 'RECEITA':
                    AccountRepository.adjust_balance(transaction.account_id, -transaction.amount)
                elif transaction.type == 'DESPESA':
                    AccountRepository.adjust_balance(transaction.account_id, transaction.amount)

            # Se tem invoice, recalcular total
            if transaction.invoice_id:
                from app.repositories.invoice_repository import InvoiceRepository
                InvoiceRepository.recalculate_total(transaction.invoice_id)

            db.session.delete(transaction)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Erro ao excluir lançamento. Tente novamente.', 'danger')

    @staticmethod
    def mark_as_realized(transaction: Transaction) -> bool:
        """Marca uma transação PREVISTO como REALIZADO e ajusta saldo."""
        if transaction.status == 'REALIZADO':
            return True

        try:
            transaction.status = 'REALIZADO'
            transaction.payment_date = date.today()

            if transaction.payment_method != 'CARTAO_CREDITO' and transaction.account_id:
                if transaction.type == 'RECEITA':
                    AccountRepository.adjust_balance(transaction.account_id, transaction.amount)
                elif transaction.type == 'DESPESA':
                    AccountRepository.adjust_balance(transaction.account_id, -transaction.amount)

            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_monthly_summary(user_id: int, month: int, year: int) -> dict:
        """Retorna resumo financeiro do mês — usando transaction_date."""
        income = TransactionRepository.sum_by_type_month(user_id, month, year, 'RECEITA', status='REALIZADO')
        expenses = TransactionRepository.sum_by_type_month(user_id, month, year, 'DESPESA', status='REALIZADO')

        # Previstos
        predicted_income = TransactionRepository.sum_by_type_month(user_id, month, year, 'RECEITA')
        predicted_expenses = TransactionRepository.sum_by_type_month(user_id, month, year, 'DESPESA')

        return {
            'income': income,
            'expenses': expenses,
            'balance': income - expenses,
            'predicted_income': predicted_income,
            'predicted_expenses': predicted_expenses,
            'predicted_balance': predicted_income - predicted_expenses,
        }

    @staticmethod
    def get_filtered(user_id: int, **kwargs) -> list:
        return TransactionRepository.get_by_user_filtered(user_id, **kwargs)
