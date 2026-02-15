from decimal import Decimal
from decimal import ROUND_DOWN

from app.modules.split_engine.schemas import ExactParticipant
from app.modules.split_engine.schemas import PercentageParticipant
from app.modules.split_engine.schemas import SplitMethod


CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _to_decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(CENT)


class SplitEngineService:
    def calculate_split(self, *, method: SplitMethod | str, total_amount: float, participants: list) -> dict[str, float]:
        total = _to_decimal(total_amount)
        if total <= 0:
            raise ValueError("total_amount must be greater than 0")

        if method == "equal":
            return self._equal_split(total, participants)
        if method == "percentage":
            return self._percentage_split(total, participants)
        if method == "exact":
            return self._exact_split(total, participants)
        raise ValueError("Unsupported split method")

    def _equal_split(self, total: Decimal, participants: list) -> dict[str, float]:
        if not participants:
            raise ValueError("participants must not be empty")
        if any(not isinstance(user_id, str) or not user_id for user_id in participants):
            raise ValueError("equal split requires a list of non-empty user ids")

        unique_participants = list(dict.fromkeys(participants))
        if len(unique_participants) != len(participants):
            raise ValueError("participants must be unique")

        count = len(participants)
        base_share = (total / count).quantize(CENT, rounding=ROUND_DOWN)
        remainder_cents = int(((total - (base_share * count)) / CENT).to_integral_value())

        result: dict[str, Decimal] = {}
        for index, user_id in enumerate(participants):
            share = base_share + (CENT if index < remainder_cents else Decimal("0"))
            result[user_id] = share

        return {user_id: float(amount) for user_id, amount in result.items()}

    def _percentage_split(self, total: Decimal, participants: list) -> dict[str, float]:
        if not participants:
            raise ValueError("participants must not be empty")

        normalized: list[PercentageParticipant] = []
        seen_user_ids: set[str] = set()
        for item in participants:
            parsed = PercentageParticipant.model_validate(item)
            if parsed.user_id in seen_user_ids:
                raise ValueError("participants must be unique")
            normalized.append(parsed)
            seen_user_ids.add(parsed.user_id)

        percentage_total = sum(Decimal(str(item.percentage)) for item in normalized)
        if percentage_total != HUNDRED:
            raise ValueError("percentage shares must sum to 100")

        result: dict[str, Decimal] = {}
        allocated = Decimal("0")
        last_user_id = normalized[-1].user_id

        for item in normalized[:-1]:
            share = (total * Decimal(str(item.percentage)) / HUNDRED).quantize(CENT, rounding=ROUND_DOWN)
            result[item.user_id] = share
            allocated += share

        result[last_user_id] = (total - allocated).quantize(CENT)
        return {user_id: float(amount) for user_id, amount in result.items()}

    def _exact_split(self, total: Decimal, participants: list) -> dict[str, float]:
        if not participants:
            raise ValueError("participants must not be empty")

        normalized: list[ExactParticipant] = []
        seen_user_ids: set[str] = set()
        for item in participants:
            parsed = ExactParticipant.model_validate(item)
            if parsed.user_id in seen_user_ids:
                raise ValueError("participants must be unique")
            normalized.append(parsed)
            seen_user_ids.add(parsed.user_id)

        total_exact = sum(_to_decimal(item.amount) for item in normalized)
        if total_exact != total:
            raise ValueError("exact shares must sum to total_amount")

        return {item.user_id: float(_to_decimal(item.amount)) for item in normalized}
