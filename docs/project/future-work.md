# Future Work

Pending initiatives that are not yet ready to implement. Consult before starting related tasks.

---

## FUTURE-001 — Knowledge base: human-in-the-loop and wiki quality

**Context:**
The `knowledge_base/` module (ingestion pipeline + keeper) is operational: it ingests YouTube transcripts, extracts knowledge cards, and the keeper maintains the wiki from those cards. However, several layers are missing before this can be considered production-ready.

### Quality of generated pages
The keeper currently uses a lightweight model (`gemini-flash-lite`) and produces pages that are too sparse. Before investing in a review workflow, the quality problem should be solved first. Options to evaluate:
- Switch the keeper to a stronger model (`flash` or `pro`)
- Increase `_MAX_LLM_CALLS` in the runner
- Critic/self-critique loop: generate → evaluate → refine → write

### Human-in-the-loop review workflow
The keeper writes pages autonomously. An admin review step is desirable before changes are visible to the Sensei agents. Conclusions from design discussions:
- **Draft mechanism**: keeper writes to `wiki/drafts/` or a `drafts` git branch; Sensei agents read from the approved state only.
- **Git as version control**: initialize `wiki/` as a local git repo; keeper commits after each run; gives history and rollback for free.
- **Review UX is the unsolved problem**: without a remote (GitHub/Gitea), the admin has no comfortable way to see changes without SSH access. Options evaluated:
  - GitHub PR workflow: clean diff UX but high operational complexity (credentials on server, webhooks, PR management).
  - Local git + SSH pull: simpler but still requires server access to review.
  - REST endpoint returning diff: functional but poor UX for markdown.
  - Telegram summary notification + approve-by-default with rollback endpoint: most pragmatic for now.
- **Recommended starting point when resuming**: implement local git for the wiki (history + rollback) and approve-by-default. Add a `POST /api/wiki/revert` endpoint to undo the last keeper commit. Defer the draft/approval gate until the review UX question is resolved.

### Semantic search for wiki pages
The Sensei agents currently discover wiki pages via `wiki_path` stored in the database. Pages created by the keeper are not registered in the database, so agents cannot find them. Planned solution: a `search_wiki(query)` tool backed by vector embeddings.
- Embedding model: `text-embedding-004` (Google, already a dependency).
- Vector store: pgvector (existing Postgres) is the preferred option — no new infrastructure.
- Index update: triggered by the keeper after each `write_wiki_page` call.
- This work should start only after the quality and review workflow are stable.

### Order of work when resuming
1. Improve keeper output quality (model + calls, or critic loop)
2. Local git for wiki (history + rollback)
3. Approve-by-default + revert endpoint
4. Semantic search with pgvector
5. Revisit the review UX once the above is stable
