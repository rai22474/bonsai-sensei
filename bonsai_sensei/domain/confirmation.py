from dataclasses import dataclass
from typing import Callable


@dataclass
class Confirmation:
    id: str
    user_id: str
    summary: str
    executor: Callable[..., dict]
    sent: bool = False

    def execute(self) -> str:
        return self.executor()