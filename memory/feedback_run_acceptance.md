---
name: feedback-run-acceptance
description: Use run_bdd_acceptance.sh for acceptance tests — user corrects any other approach
metadata:
  type: feedback
---

Use `acceptance-tests/run_bdd_acceptance.sh` from project root for all acceptance tests. Pass suite directory as single argument for a specific suite.

**Why:** User corrected attempt to invoke docker compose directly or use a non-existent script name.
**How to apply:** Always use `./acceptance-tests/run_bdd_acceptance.sh [suite-dir]`. Never docker compose directly for tests.
