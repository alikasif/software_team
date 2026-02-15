from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.entities import Expense  # noqa: E402, F401
from app.models.entities import ExpenseParticipant  # noqa: E402, F401
from app.models.entities import Group  # noqa: E402, F401
from app.models.entities import GroupMember  # noqa: E402, F401
from app.models.entities import IdempotencyKey  # noqa: E402, F401
from app.models.entities import LedgerEntry  # noqa: E402, F401
from app.models.entities import Settlement  # noqa: E402, F401
from app.models.entities import User  # noqa: E402, F401
