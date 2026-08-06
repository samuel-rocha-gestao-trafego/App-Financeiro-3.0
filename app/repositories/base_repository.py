from typing import TypeVar, Generic, Type, List, Optional, Any
from app.extensions import db

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Repository base com operações CRUD genéricas.

    Cada repository específico herda desta classe e define model_class.
    """
    model_class: Type[T] = None

    @classmethod
    def get_by_id(cls, id: int) -> Optional[T]:
        return cls.model_class.query.get(id)

    @classmethod
    def get_by_user(cls, user_id: int, **filters) -> List[T]:
        query = cls.model_class.query.filter_by(user_id=user_id, **filters)
        return query.all()

    @classmethod
    def get_one_by_user(cls, user_id: int, **filters) -> Optional[T]:
        return cls.model_class.query.filter_by(user_id=user_id, **filters).first()

    @classmethod
    def get_all(cls, **filters) -> List[T]:
        query = cls.model_class.query.filter_by(**filters)
        return query.all()

    @classmethod
    def save(cls, entity: T) -> T:
        db.session.add(entity)
        db.session.commit()
        return entity

    @classmethod
    def save_all(cls, entities: List[T]) -> List[T]:
        db.session.add_all(entities)
        db.session.commit()
        return entities

    @classmethod
    def delete(cls, entity: T) -> bool:
        try:
            db.session.delete(entity)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @classmethod
    def flush(cls, entity: T) -> T:
        db.session.add(entity)
        db.session.flush()
        return entity
