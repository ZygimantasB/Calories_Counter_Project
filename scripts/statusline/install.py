#!/usr/bin/env python3
"""Configurator and installer for Antigravity CLI and Claude Code statusline."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

# Ensure scripts directory is on sys.path for importing sister modules
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.abspath(os.path.join(_current_dir, "..", ".."))
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

try:
    from scripts.statusline.statusline_bridge import SAMPLE_PAYLOAD, run_bridge
except ImportError:  # pragma: no cover
    from statusline_bridge import SAMPLE_PAYLOAD, run_bridge

DEFAULT_SETTINGS_PATH = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
BRIDGE_SCRIPT_PATH = os.path.abspath(os.path.join(_current_dir, "statusline_bridge.py"))


def get_default_target_path() -> Path:
    """Return default target settings.json path as Path object."""
    return Path(DEFAULT_SETTINGS_PATH)


def load_settings(target_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load settings dictionary from JSON file.

    Args:
        target_path: Path to target settings file.

    Returns:
        Loaded dictionary, or empty dict if file does not exist.

    Raises:
        ValueError: If file exists but contains invalid JSON.
    """
    path = Path(target_path).expanduser()
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError(f"Settings in {target_path} is not a JSON object")
            return data
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in settings file: {target_path} ({exc})") from exc


def save_settings(target_path: Union[str, Path], settings: Dict[str, Any]) -> None:
    """
    Save settings dictionary to target path with proper formatting.

    Args:
        target_path: Path to target settings file.
        settings: Settings dictionary to write.
    """
    path = Path(target_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


def install_statusline(
    target_path: Optional[Union[str, Path]] = None,
    use_ccstatusline: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Configure statusLine hook in target settings file.

    Args:
        target_path: Target settings file path (default: ~/.gemini/antigravity-cli/settings.json).
        use_ccstatusline: Whether to pass --ccstatusline flag in bridge command.
        dry_run: If True, do not write changes to disk.

    Returns:
        Updated settings dictionary.
    """
    path = Path(target_path).expanduser() if target_path else get_default_target_path()
    settings = load_settings(path)

    cmd = f"python3 {BRIDGE_SCRIPT_PATH}"
    if use_ccstatusline:
        cmd += " --ccstatusline"

    statusline_config: Dict[str, Any] = {
        "type": "command",
        "command": cmd,
        "padding": 0,
        "enabled": True,
    }

    settings["statusLine"] = statusline_config

    if dry_run:
        print(f"[DRY-RUN] Target settings file: {path}")
        print(f"[DRY-RUN] Planned statusLine configuration:")
        print(json.dumps(settings, indent=2))
    else:
        save_settings(path, settings)
        print(f"StatusLine configured successfully in: {path}")
        print(f"Command: {cmd}")

    return settings


def uninstall_statusline(
    target_path: Optional[Union[str, Path]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Remove statusLine configuration from target settings file while preserving other keys.

    Args:
        target_path: Target settings file path.
        dry_run: If True, do not write changes to disk.

    Returns:
        Updated settings dictionary.
    """
    path = Path(target_path).expanduser() if target_path else get_default_target_path()
    if not path.exists():
        print(f"Target settings file not found: {path} (nothing to uninstall)")
        return {}

    settings = load_settings(path)

    if "statusLine" in settings:
        del settings["statusLine"]
        if dry_run:
            print(f"[DRY-RUN] Removed statusLine configuration from {path}")
            print(json.dumps(settings, indent=2))
        else:
            save_settings(path, settings)
            print(f"StatusLine configuration removed from: {path}")
    else:
        print(f"No statusLine configuration found in: {path}")

    return settings


def check_status(target_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Perform diagnostic checks on statusline installation and render live sample preview.

    Args:
        target_path: Target settings file path.

    Returns:
        Diagnostic status dictionary.
    """
    path = Path(target_path).expanduser() if target_path else get_default_target_path()

    bridge_exists = os.path.isfile(BRIDGE_SCRIPT_PATH)
    target_exists = path.exists()

    configured = False
    enabled = False
    command = ""

    if target_exists:
        try:
            settings = load_settings(path)
            sl = settings.get("statusLine")
            if isinstance(sl, dict):
                configured = True
                enabled = bool(sl.get("enabled", False))
                command = str(sl.get("command", ""))
        except Exception:
            pass

    preview = run_bridge(SAMPLE_PAYLOAD, force_native=False)

    print("=" * 60)
    print(" Antigravity / Claude Code Statusline Status Check")
    print("=" * 60)
    print(f"Bridge script path: {BRIDGE_SCRIPT_PATH} [{'OK' if bridge_exists else 'MISSING'}]")
    print(f"Settings file path: {path} [{'FOUND' if target_exists else 'NOT FOUND'}]")
    print(f"StatusLine Hook:    {'CONFIGURED' if configured else 'NOT CONFIGURED'}")
    if configured:
        print(f"  Enabled:          {enabled}")
        print(f"  Command:          {command}")
    print("-" * 60)
    print("StatusLine Preview (Sample Payload):")
    print(preview)
    print("=" * 60)

    return {
        "bridge_exists": bridge_exists,
        "target_exists": target_exists,
        "target_path": str(path),
        "configured": configured,
        "enabled": enabled,
        "command": command,
        "preview": preview,
    }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint for install.py."""
    parser = argparse.ArgumentParser(
        description="Antigravity CLI / Claude Code Statusline Configurator & Installer"
    )
    parser.add_argument(
        "-t",
        "--target",
        default=None,
        help=f"Target settings.json path (default: {DEFAULT_SETTINGS_PATH})",
    )
    parser.add_argument(
        "-u",
        "--uninstall",
        action="store_true",
        help="Remove statusLine configuration from settings.json",
    )
    parser.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="Check installation status and render sample preview",
    )
    parser.add_argument(
        "--use-ccstatusline",
        action="store_true",
        help="Configure statusline command to attempt ccstatusline bridge",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned modifications without writing to disk",
    )

    args = parser.parse_args(argv)

    try:
        if args.check:
            check_status(target_path=args.target)
            return 0

        if args.uninstall:
            uninstall_statusline(target_path=args.target, dry_run=args.dry_run)
            return 0

        install_statusline(
            target_path=args.target,
            use_ccstatusline=args.use_ccstatusline,
            dry_run=args.dry_run,
        )
        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
