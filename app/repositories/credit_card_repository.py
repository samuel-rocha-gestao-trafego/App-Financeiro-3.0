from typing import List, Optional
from app.models.credit_card import CreditCard
from app.repositories.base_repository import BaseRepository


class CreditCardRepository(BaseRepository[CreditCard]):
    model_class = CreditCard

    @classmethod
    def get_by_user(cls, user_id: int) -> List[CreditCard]:
        return CreditCard.query.filter_by(user_id=user_id).all()

    @classmethod
    def get_by_id_and_user(cls, card_id: int, user_id: int) -> Optional[CreditCard]:
        return CreditCard.query.filter_by(id=card_id, user_id=user_id).first()