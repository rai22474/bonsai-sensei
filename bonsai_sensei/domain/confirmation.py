from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Confirmation:
    id: str
    user_id: str
    summary: str
    executor: Callable[..., dict]

    def execute(self) -> str:
        return self.executor()