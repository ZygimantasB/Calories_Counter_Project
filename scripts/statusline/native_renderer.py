"""Native ANSI Statusline Renderer."""

from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict, Optional

RESET = "\033[0m"
CYAN = "\033[36m"
DARK_GRAY = "\033[90m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BRIGHT_RED = "\033[91m"
MAGENTA = "\033[35m"
BRIGHT_BLUE = "\033[94m"
WHITE = "\033[37m"

ANSI_REGEX = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from string."""
    return ANSI_REGEX.sub("", text)


def format_tokens(n: Optional[int | float | str]) -> str:
    """
    Format token count into a human-readable string.

    Examples:
        500 -> "500"
        1995 -> "2k"
        99950 -> "100k"
        218000 -> "218k"
        149200 -> "149.2k"
        1000000 -> "1.0M"
        1500000 -> "1.5M"
        2000000 -> "2.0M"
    """
    if n is None:
        return "0"
    try:
        num = float(n)
    except (ValueError, TypeError):
        return "0"

    if num <= 0:
        return "0"

    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        val = num / 1_000
        formatted = f"{val:.1f}"
        if formatted.endswith(".0"):
            return f"{int(round(val))}k"
        return f"{formatted}k"
    else:
        return str(int(num))


def render_progress_bar(percent: float, width: int = 8) -> str:
    """
    Render a progress bar using UTF-8 blocks (█) and spaces.

    Examples:
        render_progress_bar(0.0, 8) -> "        "
        render_progress_bar(50.0, 8) -> "████    "
        render_progress_bar(100.0, 8) -> "████████"
    """
    try:
        pct = float(percent)
    except (ValueError, TypeError):
        pct = 0.0

    pct = max(0.0, min(100.0, pct))
    filled = int(round((pct / 100.0) * width))
    filled = max(0, min(width, filled))
    empty = width - filled
    return "█" * filled + " " * empty


def format_duration(seconds: Optional[float | int | str]) -> str:
    """
    Format duration in seconds into a human-readable string.

    Examples:
        1740 -> "29m"
        9660 -> "2hr 41m"
        399600 -> "4d 15hr 0m"
        401280 -> "4d 15hr 28m"
    """
    if seconds is None:
        return "0m"
    try:
        total_seconds = int(float(seconds))
    except (ValueError, TypeError):
        return "0m"

    if total_seconds <= 0:
        return "0m"

    days = total_seconds // 86400
    rem = total_seconds % 86400
    hours = rem // 3600
    rem = rem % 3600
    minutes = rem // 60

    if days > 0:
        return f"{days}d {hours}hr {minutes}m"
    elif hours > 0:
        return f"{hours}hr {minutes}m"
    else:
        return f"{minutes}m"


def render_statusline(data: Dict[str, Any], enable_color: bool = True) -> str:
    """
    Render a 3-line ANSI statusline string matching the Claude Code layout.

    Args:
        data: Dictionary containing status information.
        enable_color: Whether to include ANSI color escape codes.

    Returns:
        3-line formatted statusline string.
    """
    if not isinstance(data, dict):
        data = {}

    sep = f"{DARK_GRAY} | {RESET}" if enable_color else " | "

    # -------------------------------------------------------------------------
    # Line 1: Model | Context | Cost | Branch
    # -------------------------------------------------------------------------
    model = data.get("model") or data.get("model_name") or ""
    if enable_color:
        model_part = f"{CYAN}Model: {model}{RESET}"
    else:
        model_part = f"Model: {model}"

    used_tokens = data.get("used_tokens")
    if used_tokens is None and isinstance(data.get("context"), dict):
        used_tokens = data["context"].get("used") or data["context"].get("used_tokens")
    if used_tokens is None:
        used_tokens = data.get("tokens_used", 0)

    max_tokens = data.get("max_tokens")
    if max_tokens is None and isinstance(data.get("context"), dict):
        max_tokens = data["context"].get("max") or data["context"].get("max_tokens")
    if max_tokens is None:
        max_tokens = data.get("context_window") or data.get("context_max", 0)

    try:
        used_tokens_val = float(used_tokens) if used_tokens is not None else 0.0
    except (ValueError, TypeError):
        used_tokens_val = 0.0

    try:
        max_tokens_val = float(max_tokens) if max_tokens is not None else 0.0
    except (ValueError, TypeError):
        max_tokens_val = 0.0

    context_percent = data.get("context_percent")
    if context_percent is None and isinstance(data.get("context"), dict):
        context_percent = data["context"].get("percent")

    if context_percent is None:
        if max_tokens_val > 0 and used_tokens_val > 0:
            pct_float = (used_tokens_val / max_tokens_val) * 100.0
        else:
            pct_float = 0.0
    else:
        try:
            pct_float = float(context_percent)
        except (ValueError, TypeError):
            pct_float = 0.0

    pct_int = int(round(pct_float))
    bar_str = render_progress_bar(pct_float, width=8)

    if pct_float < 50.0:
        bar_color = GREEN
    elif pct_float <= 80.0:
        bar_color = YELLOW
    else:
        bar_color = RED

    used_fmt = format_tokens(used_tokens if used_tokens is not None else 0)
    max_fmt = format_tokens(max_tokens if max_tokens is not None else 0)

    if enable_color:
        context_part = f"Context: [{bar_color}{bar_str}{RESET}] {used_fmt}/{max_fmt} ({pct_int}%)"
    else:
        context_part = f"Context: [{bar_str}] {used_fmt}/{max_fmt} ({pct_int}%)"

    cost = data.get("cost")
    if cost is None:
        cost = data.get("total_cost", 0.0)
    try:
        cost_val = float(cost)
    except (ValueError, TypeError):
        cost_val = 0.0

    if enable_color:
        cost_part = f"{GREEN}Cost: ${cost_val:.2f}{RESET}"
    else:
        cost_part = f"Cost: ${cost_val:.2f}"

    branch = data.get("branch")
    if branch is None and isinstance(data.get("git"), dict):
        branch = data["git"].get("branch")
    if branch is None:
        branch = data.get("git_branch", "")

    if not branch:
        branch_str = ""
    else:
        branch_str = str(branch)

    if len(branch_str) > 15:
        branch_disp = branch_str[:12] + "..."
    else:
        branch_disp = branch_str

    if branch_disp:
        if enable_color:
            branch_part = f"{MAGENTA}⤹ {branch_disp}{RESET}"
        else:
            branch_part = f"⤹ {branch_disp}"
    else:
        branch_part = ""

    line1_parts = [model_part, context_part, cost_part]
    if branch_part:
        line1_parts.append(branch_part)
    line1 = sep.join(line1_parts)

    # -------------------------------------------------------------------------
    # Line 2: Weekly | Weekly Reset | Block | Session | Out
    # -------------------------------------------------------------------------
    weekly_pct = data.get("weekly_percent")
    if weekly_pct is None:
        weekly_pct = data.get("weekly", 0.0)
    try:
        weekly_val = float(weekly_pct)
    except (ValueError, TypeError):
        weekly_val = 0.0

    if enable_color:
        weekly_part = f"{BRIGHT_BLUE}Weekly: {weekly_val:.1f}%{RESET}"
    else:
        weekly_part = f"Weekly: {weekly_val:.1f}%"

    weekly_reset = data.get("weekly_reset")
    if weekly_reset is None:
        weekly_reset = data.get("weekly_reset_seconds")

    if weekly_reset is not None:
        try:
            reset_duration_str = format_duration(float(weekly_reset))
        except (ValueError, TypeError):
            reset_duration_str = str(weekly_reset)
    else:
        reset_duration_str = ""

    if enable_color:
        if reset_duration_str:
            reset_part = f"{DARK_GRAY}Weekly Reset: {WHITE}{reset_duration_str}{RESET}"
        else:
            reset_part = f"{DARK_GRAY}Weekly Reset: {RESET}"
    else:
        reset_part = f"Weekly Reset: {reset_duration_str}"

    block = data.get("block")
    if block is None:
        block = data.get("block_duration") or data.get("block_seconds")

    if block is not None:
        try:
            block_str = format_duration(float(block))
        except (ValueError, TypeError):
            block_str = str(block)
    else:
        block_str = ""

    if enable_color:
        if block_str:
            block_part = f"{DARK_GRAY}Block: {WHITE}{block_str}{RESET}"
        else:
            block_part = f"{DARK_GRAY}Block: {RESET}"
    else:
        block_part = f"Block: {block_str}"

    session = data.get("session")
    if session is None:
        session = data.get("session_duration") or data.get("session_seconds")

    if session is not None:
        try:
            session_str = format_duration(float(session))
        except (ValueError, TypeError):
            session_str = str(session)
    else:
        session_str = "0m"

    if enable_color:
        session_part = f"{DARK_GRAY}Session: {WHITE}{session_str}{RESET}"
    else:
        session_part = f"Session: {session_str}"

    out = data.get("out")
    if out is None:
        out = data.get("output_tokens") or data.get("tokens_out")

    if out is not None:
        try:
            out_val = float(out)
            out_str = format_tokens(out_val)
        except (ValueError, TypeError):
            out_str = str(out)
    else:
        out_str = "0"

    if enable_color:
        out_part = f"{DARK_GRAY}Out: {WHITE}{out_str}{RESET}"
    else:
        out_part = f"Out: {out_str}"

    line2 = sep.join([weekly_part, reset_part, block_part, session_part, out_part])

    # -------------------------------------------------------------------------
    # Line 3: Prompt marker + Hints
    # -------------------------------------------------------------------------
    hints = data.get("hints")
    if not hints:
        hints = "bypass permissions on (shift+tab to cycle) · install gh for PR status · ← for agents"

    if enable_color:
        line3 = f"{BRIGHT_RED}❯❯{RESET} {WHITE}{hints}{RESET}"
    else:
        line3 = f"❯❯ {hints}"

    return f"{line1}\n{line2}\n{line3}"


if __name__ == "__main__":
    sample_default = {
        "model": "claude-3.7-sonnet",
        "used_tokens": 218000,
        "max_tokens": 1000000,
        "context_percent": 22.0,
        "cost": 12.38,
        "branch": "main",
        "weekly_percent": 20.0,
        "weekly_reset": 401280,
        "block": 9660,
        "session": 1740,
        "out": 149200,
    }

    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.argv[1])
        except Exception:
            input_data = {}
    elif not sys.stdin.isatty():
        try:
            content = sys.stdin.read().strip()
            if content:
                input_data = json.loads(content)
            else:
                input_data = sample_default
        except Exception:
            input_data = sample_default
    else:
        input_data = sample_default

    print(render_statusline(input_data))
