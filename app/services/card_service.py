from datetime import date, datetime
from decimal import Decimal
from app.models.credit_card import CreditCard
from app.repositories.credit_card_repository import CreditCardRepository
from app.services.invoice_service import InvoiceService
from app.services.transaction_service import TransactionService


class CardService:
    """
    Serviço de cartão de crédito.

    Cartão agora é meio de pagamento — não mais entidade paralela (P1).
    Compras no cartão criam Transactions com payment_method='CARTAO_CREDITO'
    vinculadas a uma Invoice.
    """

    @staticmethod
    def create_credit_card(user_id, name, closing_day=10, due_day=17, credit_limit=1000.0, color='#8b5cf6'):
        try:
            card = CreditCard(
                user_id=user_id,
                name=name,
                closing_day=closing_day,
                due_day=due_day,
                credit_limit=Decimal(str(credit_limit)),
                color=color,
                is_active=True
            )
            return CreditCardRepository.save(card)
        except Exception:
            return None

    @staticmethod
    def delete_credit_card(card_id, user_id):
        card = CreditCardRepository.get_by_id_and_user(card_id, user_id)
        if card:
            return CreditCardRepository.delete(card)
        return False

    @staticmethod
    def get_card_summary(card, user_id):
        return InvoiceService.get_card_summary(card, user_id)

    @staticmethod
    def create_card_purchase(user_id, card_id, category_id, description, amount,
                               installments_count, purchase_date, payment_method='CARTAO_CREDITO'):
        """
        Cria compra no cartão — gera transações (parceladas ou não) vinculadas à fatura.
        Substitui o antigo CardPurchase (P1).
        """
        if installments_count > 1:
            return TransactionService.create_with_installments(
                user_id=user_id,
                trans_type='DESPESA',
                description=description,
                total_amount=amount,
                installments_count=installments_count,
                first_installment_date=purchase_date,
                credit_card_id=card_id,
                category_id=category_id,
                payment_method=payment_method,
            )
        else:
            # Compra à vista no cartão — vincular à fatura
            t = TransactionService.create_transaction(
                user_id=user_id,
                trans_type='DESPESA',
                description=description,
                amount=amount,
                transaction_date=purchase_date,
                credit_card_id=card_id,
                category_id=category_id,
                payment_method=payment_method,
                status='PREVISTO',
            )
            if t:
                InvoiceService.add_transaction_to_invoice(t.id, card_id, user_id)
            return [t] if t else []
