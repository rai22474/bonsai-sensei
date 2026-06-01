from dataclasses import dataclass, field


@dataclass
class WikiReviewSession:
    review_id: str
    commit_hash: str
    pending: list[str]
    confirmed: list[str] = field(default_factory=list)
    reverted: list[str] = field(default_factory=list)

    def resolve_page(self, page_path: str, reverted: bool = False) -> None:
        if page_path in self.pending:
            self.pending.remove(page_path)
        if reverted:
            self.reverted.append(page_path)
        else:
            self.confirmed.append(page_path)

    @property
    def is_complete(self) -> bool:
        return len(self.pending) == 0
