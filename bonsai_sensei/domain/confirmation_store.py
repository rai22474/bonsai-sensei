from bonsai_sensei.domain.confirmation import Confirmation


class ConfirmationStore:
    def __init__(self):
        self._pending: dict[str, Confirmation] = {}

    def set_pending(self, user_id: str, command: Confirmation) -> None:
        self._pending[user_id] = command

    def get_pending(self, user_id: str) -> Confirmation | None:
        return self._pending.get(user_id)

    def pop_pending(self, user_id: str) -> Confirmation | None:
        return self._pending.pop(user_id, None)

    def clear_pending(self, user_id: str) -> None:
        self._pending.pop(user_id, None)
