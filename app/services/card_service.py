from datetime import date
from decimal import Decimal
from app.extensions import db
from app.models.credit_card import CreditCard
from app.models.card_purchase import CardPurchase


class CardService:

    @staticmethod
    def calculate_installment_dates(purchase_date: date, closing_day: int):
        """
        Determina o mês e ano da PRIMEIRA fatura com base no dia de compra e dia de fechamento.
        Se a compra ocorreu no dia ou após o fechamento, ela vai para a fatura do mês seguinte.
        """
        year = purchase_date.year
        month = purchase_date.month

        if purchase_date.day >= closing_day:
            month += 1
            if month > 12:
                month = 1
                year += 1

        return month, year

    @staticmethod
    def create_purchase(card_id: int, category_id: int, description: str, total_amount: float, installments_count: int, purchase_date: date) -> CardPurchase:
        card = CreditCard.query.get(card_id)
        if not card:
            raise ValueError("Cartão não encontrado.")

        first_month, first_year = CardService.calculate_installment_dates(purchase_date, card.closing_day)
        
        purchase = CardPurchase(
            credit_card_id=card_id,
            category_id=category_id,
            description=description,
            total_amount=Decimal(str(total_amount)),
            installments_count=installments_count,
            purchase_date=purchase_date,
            first_bill_month=first_month,
            first_bill_year=first_year
        )
        db.session.add(purchase)
        db.session.commit()
        return purchase

    @staticmethod
    def get_bill_total_for_month(card_id: int, month: int, year: int) -> Decimal:
        """
        Calcula o valor total da fatura de um cartão para um mês/ano específico,
        considerando todas as compras ativas cujas parcelas caem no período.
        """
        purchases = CardPurchase.query.filter_by(credit_card_id=card_id).all()
        total_bill = Decimal('0.00')

        for purchase in purchases:
            installment_val = purchase.total_amount / Decimal(purchase.installments_count)
            
            # Verifica em quais parcelas (1 até N) esta compra afeta o mês/ano solicitado
            for i in range(purchase.installments_count):
                curr_month = (purchase.first_bill_month - 1 + i) % 12 + 1
                curr_year = purchase.first_bill_year + ((purchase.first_bill_month - 1 + i) // 12)

                if curr_month == month and curr_year == year:
                    total_bill += installment_val

        return total_bill

    @staticmethod
    def get_used_credit(card_id: int) -> Decimal:
        """Calcula quanto do limite total do cartão está comprometido por compras a vencer."""
        purchases = CardPurchase.query.filter_by(credit_card_id=card_id).all()
        today = date.today()
        current_m = today.month
        current_y = today.year

        total_committed = Decimal('0.00')

        for purchase in purchases:
            installment_val = purchase.total_amount / Decimal(purchase.installments_count)
            for i in range(purchase.installments_count):
                curr_m = (purchase.first_bill_month - 1 + i) % 12 + 1
                curr_y = purchase.first_bill_year + ((purchase.first_bill_month - 1 + i) // 12)

                # Se a parcela for do mês atual ou de meses futuros, consome o limite
                if (curr_y > current_y) or (curr_y == current_y and curr_m >= current_m):
                    total_committed += installment_val

        return total_committed

    @staticmethod
    def get_card_summary(card: CreditCard):
        used_credit = CardService.get_used_credit(card.id)
        available_credit = card.credit_limit - used_credit
        
        today = date.today()
        current_bill = CardService.get_bill_total_for_month(card.id, today.month, today.year)
        
        next_m = today.month + 1 if today.month < 12 else 1
        next_y = today.year if today.month < 12 else today.year + 1
        next_bill = CardService.get_bill_total_for_month(card.id, next_m, next_y)

        return {
            'card': card,
            'used_credit': used_credit,
            'available_credit': max(Decimal('0.00'), available_credit),
            'current_bill': current_bill,
            'next_bill': next_bill
        }