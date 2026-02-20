from bonsai_sensei.domain.confirmation import Confirmation


class ConfirmationStore:
    def __init__(self):
        self._pending: dict[str, list[Confirmation]] = {}

    def set_pending(self, user_id: str, command: Confirmation) -> None:
        if user_id not in self._pending:
            self._pending[user_id] = []
        self._pending[user_id].append(command)

    def get_pending(self, user_id: str) -> Confirmation | None:
        confirmations = self._pending.get(user_id)
        return confirmations[0] if confirmations else None

    def get_all_pending(self, user_id: str) -> list[Confirmation]:
        return list(self._pending.get(user_id, []))

    def pop_pending(self, user_id: str) -> Confirmation | None:
        confirmations = self._pending.get(user_id)
        if not confirmations:
            return None
        confirmation = confirmations.pop(0)
        if not confirmations:
            del self._pending[user_id]
        return confirmation

    def clear_pending(self, user_id: str) -> None:
        self._pending.pop(user_id, None)
