import os
import subprocess
import sys
from unittest.mock import patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.statusline.git_info import get_git_status


@pytest.fixture
def empty_tmp_dir(tmp_path):
    """A directory that is definitely not a git repo."""
    non_git_dir = tmp_path / "not_a_repo"
    non_git_dir.mkdir()
    return str(non_git_dir)


@pytest.fixture
def temp_git_repo(tmp_path):
    """Creates a real temporary git repository."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    cwd = str(repo_dir)

    # Initialize git repo
    subprocess.run(["git", "init", "-b", "main"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=cwd, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=cwd, check=True)

    # Create initial commit
    file1 = repo_dir / "file1.txt"
    file1.write_text("hello")
    subprocess.run(["git", "add", "file1.txt"], cwd=cwd, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=cwd, check=True)

    return cwd, repo_dir


def test_non_git_directory(empty_tmp_dir):
    """Returns safe empty dictionary when directory is not a git repository."""
    res = get_git_status(cwd=empty_tmp_dir)
    assert res == {
        "branch": "",
        "is_dirty": False,
        "ahead": 0,
        "behind": 0,
        "detached": False,
    }


def test_non_existent_directory():
    """Returns safe empty dictionary when directory does not exist."""
    res = get_git_status(cwd="/path/that/does/not/exist/at/all/12345")
    assert res == {
        "branch": "",
        "is_dirty": False,
        "ahead": 0,
        "behind": 0,
        "detached": False,
    }


def test_clean_git_repo(temp_git_repo):
    """Returns correct status for a clean repo on a branch."""
    cwd, _ = temp_git_repo
    res = get_git_status(cwd=cwd)
    assert res["branch"] == "main"
    assert res["is_dirty"] is False
    assert res["ahead"] == 0
    assert res["behind"] == 0
    assert res["detached"] is False


def test_dirty_git_repo_untracked_file(temp_git_repo):
    """Detects untracked file as dirty."""
    cwd, repo_dir = temp_git_repo
    untracked = repo_dir / "untracked.txt"
    untracked.write_text("untracked")

    res = get_git_status(cwd=cwd)
    assert res["branch"] == "main"
    assert res["is_dirty"] is True
    assert res["detached"] is False


def test_dirty_git_repo_modified_file(temp_git_repo):
    """Detects modified tracked file as dirty."""
    cwd, repo_dir = temp_git_repo
    file1 = repo_dir / "file1.txt"
    file1.write_text("modified content")

    res = get_git_status(cwd=cwd)
    assert res["branch"] == "main"
    assert res["is_dirty"] is True
    assert res["detached"] is False


def test_dirty_git_repo_staged_file(temp_git_repo):
    """Detects staged change as dirty."""
    cwd, repo_dir = temp_git_repo
    file2 = repo_dir / "file2.txt"
    file2.write_text("staged content")
    subprocess.run(["git", "add", "file2.txt"], cwd=cwd, check=True)

    res = get_git_status(cwd=cwd)
    assert res["branch"] == "main"
    assert res["is_dirty"] is True
    assert res["detached"] is False


def test_detached_head_state(temp_git_repo):
    """Detects detached HEAD state and returns short commit SHA as branch."""
    cwd, repo_dir = temp_git_repo
    # Get commit SHA
    commit_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()
    short_sha = commit_sha[:7]

    # Detach HEAD
    subprocess.run(["git", "checkout", commit_sha], cwd=cwd, check=True, capture_output=True)

    res = get_git_status(cwd=cwd)
    assert res["detached"] is True
    assert res["branch"] == short_sha
    assert res["is_dirty"] is False


def test_ahead_behind_tracking(tmp_path):
    """Verifies ahead and behind counts with upstream tracking."""
    # Create upstream bare repo
    upstream_dir = tmp_path / "upstream.git"
    upstream_dir.mkdir()
    subprocess.run(["git", "init", "--bare", "-b", "main"], cwd=str(upstream_dir), check=True, capture_output=True)

    # Clone to local repo
    local_dir = tmp_path / "local_repo"
    subprocess.run(["git", "clone", str(upstream_dir), str(local_dir)], check=True, capture_output=True)
    cwd = str(local_dir)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=cwd, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=cwd, check=True)

    # Initial commit pushed to origin
    f = local_dir / "initial.txt"
    f.write_text("init")
    subprocess.run(["git", "add", "."], cwd=cwd, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=cwd, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=cwd, check=True, capture_output=True)

    status_sync = get_git_status(cwd=cwd)
    assert status_sync["ahead"] == 0
    assert status_sync["behind"] == 0

    # Make a commit locally (ahead by 1)
    f.write_text("change 1")
    subprocess.run(["git", "commit", "-am", "Local commit 1"], cwd=cwd, check=True)

    status_ahead = get_git_status(cwd=cwd)
    assert status_ahead["ahead"] == 1
    assert status_ahead["behind"] == 0


def test_behind_and_diverged_tracking(tmp_path):
    """Verifies behind and diverged (ahead + behind) status."""
    # Create upstream bare repo
    upstream_dir = tmp_path / "upstream.git"
    upstream_dir.mkdir()
    subprocess.run(["git", "init", "--bare", "-b", "main"], cwd=str(upstream_dir), check=True, capture_output=True)

    # Local repo 1
    repo1 = tmp_path / "repo1"
    subprocess.run(["git", "clone", str(upstream_dir), str(repo1)], check=True, capture_output=True)
    cwd1 = str(repo1)
    subprocess.run(["git", "config", "user.email", "test1@example.com"], cwd=cwd1, check=True)
    subprocess.run(["git", "config", "user.name", "Test User 1"], cwd=cwd1, check=True)

    # Initial commit
    (repo1 / "f.txt").write_text("v1")
    subprocess.run(["git", "add", "."], cwd=cwd1, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=cwd1, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=cwd1, check=True, capture_output=True)

    # Local repo 2
    repo2 = tmp_path / "repo2"
    subprocess.run(["git", "clone", str(upstream_dir), str(repo2)], check=True, capture_output=True)
    cwd2 = str(repo2)
    subprocess.run(["git", "config", "user.email", "test2@example.com"], cwd=cwd2, check=True)
    subprocess.run(["git", "config", "user.name", "Test User 2"], cwd=cwd2, check=True)

    # In repo 1, make a commit and push (now origin is ahead of repo 2)
    (repo1 / "f.txt").write_text("v2")
    subprocess.run(["git", "commit", "-am", "Remote commit 1"], cwd=cwd1, check=True)
    subprocess.run(["git", "push"], cwd=cwd1, check=True, capture_output=True)

    # In repo 2, fetch without merging
    subprocess.run(["git", "fetch"], cwd=cwd2, check=True, capture_output=True)
    status_behind = get_git_status(cwd=cwd2)
    assert status_behind["behind"] == 1
    assert status_behind["ahead"] == 0

    # In repo 2, also make local commit -> diverged (ahead 1, behind 1)
    (repo2 / "f2.txt").write_text("local")
    subprocess.run(["git", "add", "."], cwd=cwd2, check=True)
    subprocess.run(["git", "commit", "-m", "Local diverged commit"], cwd=cwd2, check=True)

    status_diverged = get_git_status(cwd=cwd2)
    assert status_diverged["ahead"] == 1
    assert status_diverged["behind"] == 1


def test_initial_empty_repo(tmp_path):
    """Verifies status on a freshly initialized git repo without commits."""
    repo_dir = tmp_path / "empty_repo"
    repo_dir.mkdir()
    cwd = str(repo_dir)
    subprocess.run(["git", "init", "-b", "main"], cwd=cwd, check=True, capture_output=True)

    res = get_git_status(cwd=cwd)
    assert res["branch"] == "main"
    assert res["is_dirty"] is False
    assert res["ahead"] == 0
    assert res["behind"] == 0
    assert res["detached"] is False


def test_cli_execution(temp_git_repo):
    """Verifies that running git_info.py as a script outputs valid JSON."""
    cwd, _ = temp_git_repo
    git_info_script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "scripts", "statusline", "git_info.py")
    )
    result = subprocess.run(
        [sys.executable, git_info_script, cwd],
        capture_output=True,
        text=True,
        check=True,
    )
    import json
    data = json.loads(result.stdout)
    assert data["branch"] == "main"
    assert data["is_dirty"] is False
    assert data["ahead"] == 0
    assert data["behind"] == 0
    assert data["detached"] is False


def test_timeout_returns_safe_dict():
    """Simulates a timeout during git execution and verifies safe fallback."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git", timeout=0.3)):
        res = get_git_status(cwd="/some/path")
        assert res == {
            "branch": "",
            "is_dirty": False,
            "ahead": 0,
            "behind": 0,
            "detached": False,
        }


def test_git_missing_returns_safe_dict():
    """Simulates git command not found (FileNotFoundError) and verifies safe fallback."""
    with patch("subprocess.run", side_effect=FileNotFoundError("No such file or directory: 'git'")):
        res = get_git_status(cwd="/some/path")
        assert res == {
            "branch": "",
            "is_dirty": False,
            "ahead": 0,
            "behind": 0,
            "detached": False,
        }


def test_general_exception_returns_safe_dict():
    """Simulates generic exception and verifies safe fallback."""
    with patch("subprocess.run", side_effect=RuntimeError("Unexpected error")):
        res = get_git_status(cwd="/some/path")
        assert res == {
            "branch": "",
            "is_dirty": False,
            "ahead": 0,
            "behind": 0,
            "detached": False,
        }


def test_default_cwd_uses_os_getcwd():
    """When cwd is None, uses current working directory."""
    res = get_git_status()
    # The Calories_Counter_Project repo is a git repo
    assert isinstance(res, dict)
    assert "branch" in res
    assert "is_dirty" in res
    assert "ahead" in res
    assert "behind" in res
    assert "detached" in res
