import subprocess
from pathlib import Path


def init_wiki_repo(wiki_root: Path) -> None:
    wiki_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "config", "--global", "safe.directory", "*"], check=True, capture_output=True)
    already_initialized = (wiki_root / ".git").exists()
    if not already_initialized:
        subprocess.run(["git", "init"], cwd=wiki_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "--local", "user.email", "dreamer@bonsai-sensei"], cwd=wiki_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "--local", "user.name", "Wiki Dreamer"], cwd=wiki_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "--local", "commit.gpgsign", "false"], cwd=wiki_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "--local", "tag.gpgsign", "false"], cwd=wiki_root, check=True, capture_output=True)
    if already_initialized:
        return
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init: wiki repository"],
        cwd=wiki_root,
        check=True,
        capture_output=True,
    )


def commit_wiki_changes(wiki_root: Path, message: str) -> str | None:
    """Stage all changes and commit. Returns the new commit hash, or None if nothing changed."""
    subprocess.run(["git", "add", "-A"], cwd=wiki_root, check=True, capture_output=True)
    nothing_staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=wiki_root, capture_output=True
    )
    if nothing_staged.returncode == 0:
        return None
    subprocess.run(["git", "commit", "-m", message], cwd=wiki_root, check=True, capture_output=True)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=wiki_root, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def get_changed_files(wiki_root: Path, commit_hash: str) -> list[str]:
    """Return paths of files changed in the given commit, relative to wiki_root."""
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", commit_hash],
        cwd=wiki_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.strip().splitlines() if line]


def get_page_diff(wiki_root: Path, page_path: str, commit_hash: str) -> str:
    """Return the unified diff for page_path introduced by commit_hash."""
    result = subprocess.run(
        ["git", "diff", f"{commit_hash}~1", commit_hash, "--", page_path],
        cwd=wiki_root,
        capture_output=True,
        text=True,
    )
    return result.stdout


def revert_page(wiki_root: Path, page_path: str, commit_hash: str) -> None:
    """Restore page_path to its state before commit_hash and create a revert commit.

    If the page was newly created by that commit, deletes it instead.
    """
    parent_exists = subprocess.run(
        ["git", "cat-file", "-e", f"{commit_hash}~1:{page_path}"],
        cwd=wiki_root,
        capture_output=True,
    )
    if parent_exists.returncode == 0:
        subprocess.run(
            ["git", "checkout", f"{commit_hash}~1", "--", page_path],
            cwd=wiki_root,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "add", "--", page_path], cwd=wiki_root, check=True, capture_output=True)
    else:
        full_path = wiki_root / page_path
        full_path.unlink(missing_ok=True)
        subprocess.run(
            ["git", "rm", "--force", "--ignore-unmatch", "--", page_path],
            cwd=wiki_root,
            check=True,
            capture_output=True,
        )
    subprocess.run(
        ["git", "commit", "-m", f"revert: dreamer change to {page_path}"],
        cwd=wiki_root,
        check=True,
        capture_output=True,
    )
