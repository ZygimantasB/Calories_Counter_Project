"""Git status extractor for statusline."""

import os
import subprocess
import sys
from typing import Any, Dict, Optional

DEFAULT_STATUS: Dict[str, Any] = {
    "branch": "",
    "is_dirty": False,
    "ahead": 0,
    "behind": 0,
    "detached": False,
}


def get_git_status(cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Get git status for repository at cwd (or current directory if None).

    Returns:
        dict with keys:
            - branch (str): branch name or short commit SHA if detached
            - is_dirty (bool): True if there are uncommitted changes or untracked files
            - ahead (int): count of commits ahead of upstream
            - behind (int): count of commits behind upstream
            - detached (bool): True if HEAD is detached
    """
    try:
        target_dir = cwd if cwd is not None else os.getcwd()
        if not os.path.isdir(target_dir):
            return dict(DEFAULT_STATUS)

        result = subprocess.run(
            ["git", "--no-optional-locks", "status", "--porcelain=v2", "--branch"],
            cwd=target_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=0.3,
        )

        if result.returncode != 0:
            return dict(DEFAULT_STATUS)

        branch = ""
        oid = ""
        is_dirty = False
        ahead = 0
        behind = 0
        detached = False

        for line in result.stdout.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            if line_str.startswith("# branch.head "):
                head_val = line_str[14:].strip()
                if head_val == "(detached)":
                    detached = True
                else:
                    branch = head_val
            elif line_str.startswith("# branch.oid "):
                oid = line_str[13:].strip()
            elif line_str.startswith("# branch.ab "):
                parts = line_str[12:].strip().split()
                for part in parts:
                    if part.startswith("+"):
                        try:
                            ahead = int(part[1:])
                        except ValueError:
                            pass
                    elif part.startswith("-"):
                        try:
                            behind = int(part[1:])
                        except ValueError:
                            pass
            elif not line_str.startswith("#"):
                is_dirty = True

        if detached:
            if oid and oid != "(initial)":
                branch = oid[:7]
            else:
                branch = "detached"

        return {
            "branch": branch,
            "is_dirty": is_dirty,
            "ahead": ahead,
            "behind": behind,
            "detached": detached,
        }
    except Exception:
        return dict(DEFAULT_STATUS)


if __name__ == "__main__":
    import json

    target = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(get_git_status(target)))
