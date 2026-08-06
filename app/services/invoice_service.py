from datetime import date
from decimal import Decimal
from calendar import monthrange
from flask import flash
from app.extensions import db
from app.models.invoice import Invoice
from app.models.credit_card import CreditCard
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.credit_card_repository import CreditCardRepository
from app.repositories.account_repository import AccountRepository
from app.services.transaction_service import TransactionService


class InvoiceService:
    """
    Serviço de gestão de faturas de cartão de crédito.

    Responsabilidades:
    - Criar/obter faturas mensais
    - Fechar e pagar faturas
    - Calcular limite disponível
    - Mapear transações de cartão para a fatura correta
    """

    @staticmethod
    def get_or_create_invoice(credit_card_id: int, user_id: int, month: int, year: int) -> Invoice:
        """Obtém ou cria fatura para o cartão no mês/ano."""
        card = CreditCardRepository.get_by_id_and_user(credit_card_id, user_id)
        if not card:
            return None

        # Calcular datas de fechamento e vencimento
        closing_day = min(card.closing_day, monthrange(year, month)[1])
        due_day = min(card.due_day, monthrange(year, month)[1])
        closing_date = date(year, month, closing_day)
        due_date = date(year, month, due_day)

        invoice = InvoiceRepository.get_or_create_for_month(
            credit_card_id, user_id, month, year, closing_date, due_date
        )
        return invoice

    @staticmethod
    def add_transaction_to_invoice(transaction_id: int, credit_card_id: int, user_id: int):
        """Vincula uma transação de cartão à fatura correta."""
        from app.models.transaction import Transaction
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return

        t_date = transaction.transaction_date
        month, year = t_date.month, t_date.year

        # Verificar se a compra foi após o fechamento → vai para a próxima fatura
        card = CreditCardRepository.get_by_id_and_user(credit_card_id, user_id)
        if card and t_date.day >= card.closing_day:
            month += 1
            if month > 12:
                month = 1
                year += 1

        invoice = InvoiceService.get_or_create_invoice(credit_card_id, user_id, month, year)
        if invoice:
            transaction.invoice_id = invoice.id
            db.session.commit()
            InvoiceRepository.recalculate_total(invoice.id)

    @staticmethod
    def pay_invoice(invoice_id: int, account_id: int, user_id: int) -> bool:
        """
        Paga a fatura: marca como PAGA, cria transação de saída na conta,
        e marca todas as transações da fatura como REALIZADAS.
        """
        try:
            invoice = Invoice.query.get(invoice_id)
            if not invoice or invoice.user_id != user_id:
                flash('Fatura não encontrada.', 'danger')
                return False

            if invoice.status == 'PAGA':
                flash('Esta fatura já foi paga.', 'warning')
                return False

            total = invoice.total_amount
            if total <= 0:
                flash('Nenhum valor a pagar nesta fatura.', 'warning')
                return False

            card = CreditCard.query.get(invoice.credit_card_id)
            card_name = card.name if card else 'Cartão'

            # Criar transação de pagamento (saída da conta)
            TransactionService.create_transaction(
                user_id=user_id,
                trans_type='DESPESA',
                description=f'Pagamento Fatura {card_name} - {invoice.month:02d}/{invoice.year}',
                amount=float(total),
                transaction_date=date.today(),
                account_id=account_id,
                status='REALIZADO',
                payment_method='TRANSFERENCIA',
            )

            # Atualizar fatura
            invoice.status = 'PAGA'
            invoice.paid_amount = total
            invoice.paid_at = date.today()
            invoice.payment_account_id = account_id

            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            flash('Erro ao pagar fatura. Tente novamente.', 'danger')
            return False

    @staticmethod
    def get_card_used_credit(credit_card_id: int) -> Decimal:
        """Calcula crédito comprometido (faturas abertas + fechadas não pagas)."""
        invoices = Invoice.query.filter(
            Invoice.credit_card_id == credit_card_id,
            Invoice.status.in_(['ABERTA', 'FECHADA'])
        ).all()

        return sum((inv.total_amount - inv.paid_amount for inv in invoices), Decimal('0.00'))

    @staticmethod
    def get_card_summary(card, user_id: int) -> dict:
        """Retorna resumo completo do cartão."""
        used = InvoiceService.get_card_used_credit(card.id)
        available = max(Decimal('0.00'), (card.credit_limit or Decimal('0')) - used)

        # Fatura atual
        from datetime import datetime
        today = datetime.utcnow().date()
        current_invoice = InvoiceRepository.get_by_card_month(card.id, today.month, today.year)

        # Próxima fatura
        next_m = today.month + 1 if today.month < 12 else 1
        next_y = today.year if today.month < 12 else today.year + 1
        next_invoice = InvoiceRepository.get_by_card_month(card.id, next_m, next_y)

        return {
            'card': card,
            'used_credit': used,
            'available_credit': available,
            'current_invoice': current_invoice,
            'next_invoice': next_invoice,
        }

    @staticmethod
    def get_invoice_transactions(invoice_id: int, user_id: int) -> list:
        """Retorna transações de uma fatura, verificando ownership."""
        invoice = Invoice.query.get(invoice_id)
        if not invoice or invoice.user_id != user_id:
            return []
        return InvoiceRepository.get_transactions(invoice_id)
