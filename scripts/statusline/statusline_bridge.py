#!/usr/bin/env python3
"""JSON Normalizer and ccstatusline Bridge for statusline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import shutil
import subprocess
import sys
from typing import Any, Dict, Optional

# Ensure project root is on sys.path for robust imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.abspath(os.path.join(_current_dir, "..", ".."))
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

try:
    from scripts.statusline.git_info import get_git_status
    from scripts.statusline.native_renderer import render_statusline
except ImportError:  # pragma: no cover
    from git_info import get_git_status
    from native_renderer import render_statusline

DEFAULT_MODEL = "Gemini 3.7 Flash"
DEFAULT_MAX_TOKENS = 1_000_000
DEFAULT_HINTS = "bypass permissions on (shift+tab to cycle) · install gh for PR status · ← for agents"

SAMPLE_PAYLOAD: Dict[str, Any] = {
    "modelName": "gemini-2.5-pro",
    "context_window": {
        "total_input_tokens": 218000,
        "total_output_tokens": 149200,
        "max_tokens": 1000000,
        "used_percentage": 21.8,
    },
    "cost": 12.38,
    "branch": "main",
    "rate_limits": {
        "seven_day": {
            "used_percentage": 20.0,
            "resets_in": 401280,
        },
        "block": {
            "resets_in": 9660,
        },
    },
    "session_duration": 1740,
    "hints": DEFAULT_HINTS,
}


def _parse_resets_at(val: Any) -> Optional[int]:
    """Parse resets_at/resets_in into duration seconds."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        val_str = val.strip()
        try:
            return int(float(val_str))
        except ValueError:
            pass
        try:
            iso_str = val_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            delta = (dt - now).total_seconds()
            return max(0, int(delta))
        except Exception:
            return None
    return None


def normalize_payload(raw_data: Dict[str, Any], cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Normalize raw statusline payload from Antigravity CLI, Claude Code, or custom formats.

    Args:
        raw_data: Raw JSON dictionary from stdin or arguments.
        cwd: Optional working directory for git status resolution.

    Returns:
        Canonical normalized dictionary.
    """
    if not isinstance(raw_data, dict):
        raw_data = {}

    # -------------------------------------------------------------------------
    # 1. Workspace Directory
    # -------------------------------------------------------------------------
    workspace_dir = cwd or raw_data.get("cwd")
    if not workspace_dir:
        workspace_paths = raw_data.get("workspacePaths")
        if isinstance(workspace_paths, list) and len(workspace_paths) > 0 and workspace_paths[0]:
            workspace_dir = str(workspace_paths[0])
    if not workspace_dir and isinstance(raw_data.get("workspace"), dict):
        ws_dict = raw_data["workspace"]
        workspace_dir = ws_dict.get("project_dir") or ws_dict.get("path") or ws_dict.get("cwd")
    if not workspace_dir:
        workspace_dir = raw_data.get("project_dir") or raw_data.get("workspace_dir") or raw_data.get("workspace_path")
    if not workspace_dir:
        try:
            workspace_dir = os.getcwd()
        except Exception:
            workspace_dir = None

    # -------------------------------------------------------------------------
    # 2. Model Name
    # -------------------------------------------------------------------------
    model = ""
    raw_model = raw_data.get("model")
    if isinstance(raw_model, dict):
        model = raw_model.get("display_name") or raw_model.get("id") or raw_model.get("name") or ""
    elif isinstance(raw_model, str):
        model = raw_model

    if not model:
        model = (
            raw_data.get("modelName")
            or raw_data.get("model_name")
            or raw_data.get("model_id")
            or raw_data.get("display_name")
            or ""
        )

    if not model or not str(model).strip():
        model = DEFAULT_MODEL
    else:
        model = str(model).strip()

    # -------------------------------------------------------------------------
    # 3. Context & Tokens
    # -------------------------------------------------------------------------
    cw = raw_data.get("context_window") if isinstance(raw_data.get("context_window"), dict) else {}
    tokens = raw_data.get("tokens") if isinstance(raw_data.get("tokens"), dict) else {}
    ctx = raw_data.get("context") if isinstance(raw_data.get("context"), dict) else {}

    # Used tokens
    used_tokens_candidates = [
        cw.get("total_input_tokens"),
        cw.get("input_tokens"),
        cw.get("used_tokens"),
        cw.get("used"),
        tokens.get("input_tokens"),
        tokens.get("input"),
        tokens.get("total_input_tokens"),
        ctx.get("used"),
        ctx.get("used_tokens"),
        raw_data.get("used_tokens"),
        raw_data.get("tokens_used"),
        raw_data.get("input_tokens"),
    ]
    used_tokens = 0
    for cand in used_tokens_candidates:
        if cand is not None:
            try:
                used_tokens = int(float(cand))
                break
            except (ValueError, TypeError):
                continue

    # Max tokens
    max_tokens_candidates = [
        cw.get("max_tokens"),
        cw.get("limit"),
        cw.get("context_window_size"),
        ctx.get("max"),
        ctx.get("max_tokens"),
        raw_data.get("max_tokens"),
        raw_data.get("context_max"),
        raw_data.get("context_window") if not isinstance(raw_data.get("context_window"), dict) else None,
    ]
    max_tokens = DEFAULT_MAX_TOKENS
    for cand in max_tokens_candidates:
        if cand is not None:
            try:
                val = int(float(cand))
                if val > 0:
                    max_tokens = val
                    break
            except (ValueError, TypeError):
                continue

    # Output tokens
    output_tokens_candidates = [
        cw.get("total_output_tokens"),
        cw.get("output_tokens"),
        tokens.get("output_tokens"),
        tokens.get("output"),
        tokens.get("total_output_tokens"),
        raw_data.get("output_tokens"),
        raw_data.get("tokens_out"),
        raw_data.get("out"),
    ]
    output_tokens = 0
    for cand in output_tokens_candidates:
        if cand is not None:
            try:
                output_tokens = int(float(cand))
                break
            except (ValueError, TypeError):
                continue

    # Context percent
    context_percent = None
    percent_candidates = [
        cw.get("used_percentage"),
        cw.get("percent"),
        ctx.get("percent"),
        raw_data.get("context_percent"),
    ]
    for cand in percent_candidates:
        if cand is not None:
            try:
                context_percent = float(cand)
                break
            except (ValueError, TypeError):
                continue

    if context_percent is None:
        if max_tokens > 0 and used_tokens > 0:
            context_percent = round((used_tokens / max_tokens) * 100.0, 1)
        else:
            context_percent = 0.0

    # -------------------------------------------------------------------------
    # 4. Cost
    # -------------------------------------------------------------------------
    cost = 0.0
    cost_field = raw_data.get("cost")
    if isinstance(cost_field, dict):
        cost_val = cost_field.get("total_cost_usd") or cost_field.get("cost") or cost_field.get("total")
    else:
        cost_val = cost_field

    cost_candidates = [
        cost_val,
        raw_data.get("session_cost"),
        raw_data.get("cost_usd"),
        raw_data.get("spend"),
        raw_data.get("total_cost"),
    ]
    for cand in cost_candidates:
        if cand is not None:
            try:
                cost = float(cand)
                break
            except (ValueError, TypeError):
                continue

    # -------------------------------------------------------------------------
    # 5. Git Branch & Status
    # -------------------------------------------------------------------------
    git_dict = raw_data.get("git") if isinstance(raw_data.get("git"), dict) else {}
    explicit_branch = raw_data.get("branch") or git_dict.get("branch") or raw_data.get("git_branch")
    is_dirty = raw_data.get("is_dirty") if "is_dirty" in raw_data else git_dict.get("is_dirty", False)
    ahead = raw_data.get("ahead") if "ahead" in raw_data else git_dict.get("ahead", 0)
    behind = raw_data.get("behind") if "behind" in raw_data else git_dict.get("behind", 0)

    if explicit_branch and str(explicit_branch).strip():
        branch = str(explicit_branch).strip()
    else:
        git_status = get_git_status(workspace_dir)
        branch = git_status.get("branch", "")
        is_dirty = git_status.get("is_dirty", False)
        ahead = git_status.get("ahead", 0)
        behind = git_status.get("behind", 0)

    # -------------------------------------------------------------------------
    # 6. Quota / Rate limits
    # -------------------------------------------------------------------------
    rate_limits = raw_data.get("rate_limits") if isinstance(raw_data.get("rate_limits"), dict) else {}
    seven_day = rate_limits.get("seven_day") if isinstance(rate_limits.get("seven_day"), dict) else {}
    quota = raw_data.get("quota") if isinstance(raw_data.get("quota"), dict) else {}
    block_dict = rate_limits.get("block") if isinstance(rate_limits.get("block"), dict) else {}

    weekly_percent = 0.0
    weekly_candidates = [
        seven_day.get("used_percentage"),
        rate_limits.get("used_percentage"),
        quota.get("weekly_percentage"),
        quota.get("used_percentage"),
        raw_data.get("weekly_percent"),
        raw_data.get("weekly"),
    ]
    for cand in weekly_candidates:
        if cand is not None:
            try:
                weekly_percent = float(cand)
                break
            except (ValueError, TypeError):
                continue

    weekly_reset_val = (
        seven_day.get("resets_in")
        or seven_day.get("resets_at")
        or quota.get("resets_in")
        or quota.get("resets_at")
        or raw_data.get("weekly_reset")
        or raw_data.get("weekly_reset_seconds")
        or raw_data.get("resets_in")
        or raw_data.get("resets_at")
    )
    weekly_reset = _parse_resets_at(weekly_reset_val)
    if weekly_reset is None and weekly_reset_val is not None:
        weekly_reset = weekly_reset_val

    block_val = (
        block_dict.get("resets_in")
        or block_dict.get("duration")
        or raw_data.get("block")
        or raw_data.get("block_duration")
        or raw_data.get("block_seconds")
    )
    block = _parse_resets_at(block_val)
    if block is None and block_val is not None:
        block = block_val

    # -------------------------------------------------------------------------
    # 7. Timers & Hints
    # -------------------------------------------------------------------------
    session_val = (
        raw_data.get("session")
        or raw_data.get("session_duration")
        or raw_data.get("session_seconds")
        or raw_data.get("elapsed_time")
        or raw_data.get("elapsed")
    )
    session = _parse_resets_at(session_val)
    if session is None and session_val is not None:
        session = session_val
    if session is None:
        session = 0

    hints = raw_data.get("hints") or DEFAULT_HINTS
    mode = raw_data.get("mode")

    return {
        "model": model,
        "used_tokens": used_tokens,
        "max_tokens": max_tokens,
        "output_tokens": output_tokens,
        "out": output_tokens,
        "context_percent": context_percent,
        "cost": cost,
        "branch": branch,
        "is_dirty": bool(is_dirty),
        "ahead": int(ahead) if ahead is not None else 0,
        "behind": int(behind) if behind is not None else 0,
        "weekly_percent": weekly_percent,
        "weekly_reset": weekly_reset,
        "block": block,
        "session": session,
        "hints": hints,
        "mode": mode,
        "workspace_dir": workspace_dir,
    }


def run_bridge(
    raw_data: Dict[str, Any],
    force_native: bool = False,
    use_ccstatusline: bool = False,
    cwd: Optional[str] = None,
    enable_color: bool = True,
) -> str:
    """
    Run statusline renderer, optionally bridging via ccstatusline with fallback to native.

    Args:
        raw_data: Raw input dictionary.
        force_native: Force direct native rendering.
        use_ccstatusline: Attempt ccstatusline execution.
        cwd: Working directory override.
        enable_color: Whether to enable ANSI colors in native renderer.

    Returns:
        Formatted statusline string.
    """
    normalized = normalize_payload(raw_data, cwd=cwd)

    if force_native or not use_ccstatusline:
        return render_statusline(normalized, enable_color=enable_color)

    # Fast-path check for ccstatusline/npx binaries before attempting subprocess
    ccstatusline_bin = shutil.which("ccstatusline")
    npx_bin = shutil.which("npx")
    if not ccstatusline_bin and not npx_bin:
        return render_statusline(normalized, enable_color=enable_color)

    # Attempt ccstatusline bridge
    cc_payload = {
        "model": {
            "id": normalized["model"],
            "display_name": normalized["model"],
        },
        "context_window": {
            "total_input_tokens": normalized["used_tokens"],
            "total_output_tokens": normalized["output_tokens"],
            "max_tokens": normalized["max_tokens"],
            "used_percentage": normalized["context_percent"],
        },
        "cost": {
            "total_cost_usd": normalized["cost"],
        },
        "workspace": {
            "project_dir": normalized.get("workspace_dir") or "",
        },
        "git": {
            "branch": normalized.get("branch", ""),
            "is_dirty": normalized.get("is_dirty", False),
            "ahead": normalized.get("ahead", 0),
            "behind": normalized.get("behind", 0),
        },
        "rate_limits": {
            "seven_day": {
                "used_percentage": normalized.get("weekly_percent", 0.0),
                "resets_in": normalized.get("weekly_reset"),
            }
        },
    }

    try:
        input_json = json.dumps(cc_payload)
        commands_to_try = []
        if ccstatusline_bin:
            commands_to_try.append(["ccstatusline"])
        if npx_bin:
            commands_to_try.append(["npx", "--no-install", "ccstatusline"])

        rendered = None
        for cmd in commands_to_try:
            try:
                proc = subprocess.run(
                    cmd,
                    input=input_json,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=0.3,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    rendered = proc.stdout.rstrip("\r\n")
                    break
            except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired):
                continue

        if rendered:
            return rendered

    except Exception:
        pass

    # Fallback to native renderer
    return render_statusline(normalized, enable_color=enable_color)


def main() -> None:
    """CLI entry point for statusline_bridge."""
    parser = argparse.ArgumentParser(description="Antigravity Statusline Bridge & Normalizer")
    parser.add_argument("payload", nargs="?", default=None, help="Optional raw JSON payload string")
    parser.add_argument("--native", action="store_true", help="Force native ANSI renderer")
    parser.add_argument("--ccstatusline", action="store_true", help="Attempt ccstatusline bridging")
    parser.add_argument("--json", action="store_true", help="Output normalized JSON payload")
    parser.add_argument("--sample", action="store_true", help="Use sample data payload")
    parser.add_argument("--cwd", default=None, help="Working directory override")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color codes")

    args = parser.parse_args()

    raw_data: Dict[str, Any] = {}

    if args.sample:
        raw_data = SAMPLE_PAYLOAD
    elif args.payload:
        try:
            raw_data = json.loads(args.payload)
        except Exception:
            raw_data = {}
    elif not sys.stdin.isatty():
        try:
            content = sys.stdin.read().strip()
            if content:
                raw_data = json.loads(content)
        except Exception:
            raw_data = {}

    if args.json:
        normalized = normalize_payload(raw_data, cwd=args.cwd)
        print(json.dumps(normalized, indent=2))
    else:
        output = run_bridge(
            raw_data,
            force_native=args.native,
            use_ccstatusline=args.ccstatusline,
            cwd=args.cwd,
            enable_color=not args.no_color,
        )
        print(output)


if __name__ == "__main__":
    main()
