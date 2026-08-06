from typing import List, Optional
from app.models.recurring_bill import RecurringBill
from app.repositories.base_repository import BaseRepository


class RecurringRepository(BaseRepository[RecurringBill]):
    model_class = RecurringBill

    @classmethod
    def get_active_by_user(cls, user_id: int) -> List[RecurringBill]:
        return RecurringBill.query.filter_by(
            user_id=user_id, is_active=True
        ).order_by(RecurringBill.due_day.asc()).all()

    @classmethod
    def get_by_id_and_user(cls, bill_id: int, user_id: int) -> Optional[RecurringBill]:
        return RecurringBill.query.filter_by(id=bill_id, user_id=user_id).first()
