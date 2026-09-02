"""Integration and end-to-end tests for statusline bridge and installer."""

from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.statusline.statusline_bridge import (
    SAMPLE_PAYLOAD,
    _parse_resets_at,
    normalize_payload,
    run_bridge,
)
from scripts.statusline.install import (
    DEFAULT_SETTINGS_PATH,
    check_status,
    get_default_target_path,
    install_statusline,
    load_settings,
    main as install_main,
    save_settings,
    uninstall_statusline,
)

SCRIPT_DIR = Path(__file__).parent.parent / "scripts" / "statusline"
BRIDGE_PY = str(SCRIPT_DIR / "statusline_bridge.py")
INSTALL_PY = str(SCRIPT_DIR / "install.py")


# =============================================================================
# 1. Subprocess End-to-End Pipeline Tests
# =============================================================================

def test_e2e_antigravity_payload_stdin():
    """Verify piping realistic Antigravity payload via stdin produces 3-line output."""
    payload = {
        "modelName": "gemini-2.5-pro",
        "context_window": {
            "total_input_tokens": 125000,
            "total_output_tokens": 8500,
            "max_tokens": 1000000,
            "used_percentage": 12.5,
        },
        "cost": 3.42,
        "rate_limits": {
            "seven_day": {
                "used_percentage": 18.2,
                "resets_in": 7200,
            },
            "block": {
                "resets_in": 900,
            },
        },
        "session_duration": 1500,
        "hints": "bypass permissions on (shift+tab to cycle)",
    }

    cmd = [sys.executable, BRIDGE_PY, "--native"]
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=3.0,
    )

    assert proc.returncode == 0
    lines = proc.stdout.strip().split("\n")
    assert len(lines) == 3

    # Line 1: Model, Context, Cost
    assert "gemini-2.5-pro" in lines[0]
    assert "125k/1.0M" in lines[0] or "12%" in lines[0]
    assert "$3.42" in lines[0]

    # Line 2: Weekly, Block, Session
    assert "18.2%" in lines[1]
    assert "2h" in lines[1]
    assert "15m" in lines[1]
    assert "25m" in lines[1]

    # Line 3: Hints
    assert "bypass permissions on" in lines[2]


def test_e2e_claude_code_payload_stdin():
    """Verify piping realistic Claude Code format payload via stdin produces 3-line output."""
    payload = {
        "model": {
            "id": "claude-3-7-sonnet-20250219",
            "display_name": "Claude 3.7 Sonnet",
        },
        "tokens": {
            "input_tokens": 300000,
            "output_tokens": 25000,
        },
        "context_window": {
            "limit": 1000000,
            "used_percentage": 30.0,
        },
        "cost_usd": 15.60,
        "git": {
            "branch": "feature/integration-tests",
            "is_dirty": True,
            "ahead": 1,
            "behind": 0,
        },
        "quota": {
            "weekly_percentage": 42.0,
        },
        "resets_in": 86400,
        "elapsed_time": 3600,
        "hints": "custom hint message",
    }

    cmd = [sys.executable, BRIDGE_PY, "--native"]
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=3.0,
    )

    assert proc.returncode == 0
    lines = proc.stdout.strip().split("\n")
    assert len(lines) == 3

    # Line 1
    assert "Claude 3.7 Sonnet" in lines[0]
    assert "300k/1.0M" in lines[0] or "30%" in lines[0]
    assert "$15.60" in lines[0]
    assert "feature/inte" in lines[0]

    # Line 2
    assert "42.0%" in lines[1]
    assert "1d" in lines[1] or "24h" in lines[1]
    assert "1h" in lines[1]

    # Line 3
    assert "custom hint message" in lines[2]


def test_e2e_sample_flag():
    """Verify --sample flag executes and outputs 3 lines."""
    cmd = [sys.executable, BRIDGE_PY, "--sample"]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=3.0,
    )
    assert proc.returncode == 0
    lines = proc.stdout.strip().split("\n")
    assert len(lines) == 3
    assert "gemini-2.5-pro" in lines[0]
    assert "$12.38" in lines[0]


def test_e2e_json_flag():
    """Verify --json flag outputs normalized JSON."""
    cmd = [sys.executable, BRIDGE_PY, "--sample", "--json"]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=3.0,
    )
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert parsed["model"] == "gemini-2.5-pro"
    assert parsed["cost"] == 12.38
    assert parsed["context_percent"] == 21.8


def test_e2e_no_color_flag():
    """Verify --no-color flag strips all ANSI escape codes."""
    cmd = [sys.executable, BRIDGE_PY, "--sample", "--no-color"]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=3.0,
    )
    assert proc.returncode == 0
    assert "\033[" not in proc.stdout
    lines = proc.stdout.strip().split("\n")
    assert len(lines) == 3


def test_e2e_empty_stdin_fallback():
    """Verify empty stdin produces valid default output without crashing."""
    cmd = [sys.executable, BRIDGE_PY]
    proc = subprocess.run(
        cmd,
        input="",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=3.0,
    )
    assert proc.returncode == 0
    lines = proc.stdout.strip().split("\n")
    assert len(lines) == 3
    assert "Model:" in lines[0]


def test_e2e_malformed_stdin_fallback():
    """Verify malformed JSON on stdin falls back cleanly."""
    cmd = [sys.executable, BRIDGE_PY]
    proc = subprocess.run(
        cmd,
        input="{not valid json:",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=3.0,
    )
    assert proc.returncode == 0
    lines = proc.stdout.strip().split("\n")
    assert len(lines) == 3
    assert "Model:" in lines[0]


# =============================================================================
# 2. Bridge Polish Tests (_parse_resets_at naive datetime & shutil.which)
# =============================================================================

def test_parse_resets_at_naive_iso_datetime():
    """Verify naive ISO datetime string is safely handled by assuming UTC."""
    future_time = datetime.now(timezone.utc) + timedelta(seconds=1800)
    naive_iso_str = future_time.strftime("%Y-%m-%dT%H:%M:%S")

    parsed = _parse_resets_at(naive_iso_str)
    assert parsed is not None
    assert 1780 <= parsed <= 1820


def test_parse_resets_at_past_iso_datetime():
    """Verify past ISO datetime returns 0."""
    past_time = datetime.now(timezone.utc) - timedelta(seconds=1800)
    iso_str = past_time.isoformat()
    assert _parse_resets_at(iso_str) == 0


def test_run_bridge_fast_path_when_binaries_missing():
    """Verify run_bridge fast-paths to native renderer when ccstatusline & npx are missing."""
    with patch("shutil.which", return_value=None):
        with patch("subprocess.run") as mock_subproc:
            rendered = run_bridge({"model": "fastpath-test", "branch": "main"}, use_ccstatusline=True)
            mock_subproc.assert_not_called()
            assert "Model: fastpath-test" in rendered


# =============================================================================
# 3. Installer Tests (install.py)
# =============================================================================

def test_get_default_target_path():
    """Test get_default_target_path returns Path object pointing to DEFAULT_SETTINGS_PATH."""
    default_path = get_default_target_path()
    assert str(default_path) == DEFAULT_SETTINGS_PATH
    assert isinstance(default_path, Path)


def test_installer_fresh_install(tmp_path):
    """Test installing statusLine configuration into a new settings.json file."""
    from scripts.statusline.install import install_statusline

    target_file = tmp_path / "settings.json"
    assert not target_file.exists()

    result = install_statusline(target_path=target_file, use_ccstatusline=False, dry_run=False)
    assert target_file.exists()

    with open(target_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert "statusLine" in saved_data
    assert saved_data["statusLine"]["type"] == "command"
    assert saved_data["statusLine"]["padding"] == 0
    assert saved_data["statusLine"]["enabled"] is True
    assert saved_data["statusLine"]["command"].startswith('python3 "')
    assert "statusline_bridge.py\"" in saved_data["statusLine"]["command"]
    assert "--ccstatusline" not in saved_data["statusLine"]["command"]
    assert result == saved_data


def test_installer_use_ccstatusline_flag(tmp_path):
    """Test installing with --use-ccstatusline adds flag to command."""
    from scripts.statusline.install import install_statusline

    target_file = tmp_path / "settings.json"

    install_statusline(target_path=target_file, use_ccstatusline=True, dry_run=False)

    with open(target_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["statusLine"]["command"].endswith('statusline_bridge.py" --ccstatusline')


def test_installer_preserves_existing_settings(tmp_path):
    """Test installing preserves other existing settings."""
    from scripts.statusline.install import install_statusline

    target_file = tmp_path / "settings.json"
    initial_data = {
        "theme": "dark",
        "editor": "code",
        "customKey": {"nested": 123},
        "statusLine": {"old": "data"},
    }
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, indent=2)

    install_statusline(target_path=target_file, use_ccstatusline=False, dry_run=False)

    with open(target_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["theme"] == "dark"
    assert saved_data["editor"] == "code"
    assert saved_data["customKey"] == {"nested": 123}
    assert saved_data["statusLine"]["type"] == "command"
    assert saved_data["statusLine"]["enabled"] is True


def test_installer_dry_run(tmp_path):
    """Test --dry-run does not modify the target file on disk."""
    from scripts.statusline.install import install_statusline

    target_file = tmp_path / "settings.json"
    initial_data = {"existing": "setting"}
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, indent=2)

    res = install_statusline(target_path=target_file, dry_run=True)
    assert "statusLine" in res

    with open(target_file, "r", encoding="utf-8") as f:
        on_disk = json.load(f)

    assert "statusLine" not in on_disk
    assert on_disk == {"existing": "setting"}


def test_installer_uninstall(tmp_path):
    """Test uninstalling statusLine configuration."""
    from scripts.statusline.install import uninstall_statusline

    target_file = tmp_path / "settings.json"
    initial_data = {
        "statusLine": {"type": "command", "command": "something"},
        "keep_me": "yes",
    }
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, indent=2)

    uninstall_statusline(target_path=target_file, dry_run=False)

    with open(target_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert "statusLine" not in saved_data
    assert saved_data["keep_me"] == "yes"


def test_installer_uninstall_dry_run(tmp_path):
    """Test uninstall with dry_run does not modify disk."""
    from scripts.statusline.install import uninstall_statusline

    target_file = tmp_path / "settings.json"
    initial_data = {
        "statusLine": {"type": "command", "command": "something"},
    }
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, indent=2)

    uninstall_statusline(target_path=target_file, dry_run=True)

    with open(target_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert "statusLine" in saved_data


def test_installer_uninstall_non_existent_file(tmp_path):
    """Test uninstall on non-existent file runs gracefully."""
    from scripts.statusline.install import uninstall_statusline

    target_file = tmp_path / "does_not_exist.json"
    res = uninstall_statusline(target_path=target_file, dry_run=False)
    assert res == {}


def test_installer_check_status_configured(tmp_path):
    """Test check_status reporting when statusLine is installed."""
    from scripts.statusline.install import check_status, install_statusline

    target_file = tmp_path / "settings.json"
    install_statusline(target_path=target_file, dry_run=False)

    status = check_status(target_path=target_file)
    assert status["target_exists"] is True
    assert status["configured"] is True
    assert status["enabled"] is True
    assert "statusline_bridge.py" in status["command"]
    assert "preview" in status
    assert len(status["preview"].split("\n")) == 3


def test_installer_check_status_not_configured(tmp_path):
    """Test check_status reporting when statusLine is not installed."""
    from scripts.statusline.install import check_status

    target_file = tmp_path / "empty_settings.json"
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump({"foo": "bar"}, f)

    status = check_status(target_path=target_file)
    assert status["target_exists"] is True
    assert status["configured"] is False
    assert status["enabled"] is False


def test_installer_non_existent_directory_creation(tmp_path):
    """Test installing creates deeply nested parent directories."""
    from scripts.statusline.install import install_statusline

    target_file = tmp_path / "nested" / "sub" / "dir" / "settings.json"
    assert not target_file.parent.exists()

    install_statusline(target_path=target_file, dry_run=False)
    assert target_file.exists()


def test_installer_corrupted_json(tmp_path):
    """Test load_settings raises ValueError on corrupted JSON file."""
    from scripts.statusline.install import load_settings

    target_file = tmp_path / "corrupt.json"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("{ invalid json content ...")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_settings(target_file)


# =============================================================================
# 4. Installer CLI Tests via subprocess
# =============================================================================

def test_installer_cli_install(tmp_path):
    """Test install.py CLI invocation."""
    target_file = tmp_path / "cli_settings.json"
    cmd = [sys.executable, INSTALL_PY, "--target", str(target_file)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3.0)
    assert proc.returncode == 0
    assert target_file.exists()


def test_installer_cli_dry_run(tmp_path):
    """Test install.py CLI with --dry-run."""
    target_file = tmp_path / "cli_dry_settings.json"
    cmd = [sys.executable, INSTALL_PY, "--target", str(target_file), "--dry-run"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3.0)
    assert proc.returncode == 0
    assert not target_file.exists()


def test_installer_cli_check(tmp_path):
    """Test install.py CLI with --check."""
    from scripts.statusline.install import install_statusline

    target_file = tmp_path / "cli_check_settings.json"
    install_statusline(target_path=target_file)

    cmd = [sys.executable, INSTALL_PY, "--target", str(target_file), "--check"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3.0)
    assert proc.returncode == 0
    assert "StatusLine Preview" in proc.stdout or "Model:" in proc.stdout


def test_installer_cli_uninstall(tmp_path):
    """Test install.py CLI with --uninstall."""
    from scripts.statusline.install import install_statusline

    target_file = tmp_path / "cli_uninstall_settings.json"
    install_statusline(target_path=target_file)

    cmd = [sys.executable, INSTALL_PY, "--target", str(target_file), "--uninstall"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3.0)
    assert proc.returncode == 0

    with open(target_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "statusLine" not in data


def test_installer_cli_corrupted_json_error(tmp_path):
    """Test install.py CLI handles corrupted JSON with non-zero exit code and error message."""
    target_file = tmp_path / "corrupt_cli.json"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("{ invalid json")

    cmd = [sys.executable, INSTALL_PY, "--target", str(target_file)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3.0)
    assert proc.returncode != 0
    assert "Error" in proc.stderr or "Invalid JSON" in proc.stderr or "Error" in proc.stdout or "Invalid JSON" in proc.stdout


# =============================================================================
# 5. Direct Python API & Edge Cases for Installer
# =============================================================================

def test_load_settings_empty_file(tmp_path):
    """Test load_settings on an empty file returns empty dict."""
    target_file = tmp_path / "empty.json"
    target_file.touch()
    assert load_settings(target_file) == {}


def test_load_settings_non_dict_json(tmp_path):
    """Test load_settings on JSON list or scalar raises ValueError."""
    target_file = tmp_path / "list.json"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("[1, 2, 3]")
    with pytest.raises(ValueError, match="not a JSON object"):
        load_settings(target_file)


def test_uninstall_when_statusline_key_missing(tmp_path):
    """Test uninstalling when target file exists but has no statusLine key."""
    target_file = tmp_path / "no_sl.json"
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump({"other_key": 42}, f)
    res = uninstall_statusline(target_path=target_file, dry_run=False)
    assert res == {"other_key": 42}


def test_check_status_with_corrupted_file(tmp_path):
    """Test check_status gracefully handles corrupted target file."""
    target_file = tmp_path / "corrupt_check.json"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("{ broken json")
    status = check_status(target_path=target_file)
    assert status["target_exists"] is True
    assert status["configured"] is False


def test_install_main_direct_invocation(tmp_path):
    """Test install.py main() function called directly within Python."""
    target_file = tmp_path / "direct_main.json"

    # Install
    code = install_main(["--target", str(target_file)])
    assert code == 0
    assert target_file.exists()

    # Check
    code = install_main(["--target", str(target_file), "--check"])
    assert code == 0

    # Dry-run uninstall
    code = install_main(["--target", str(target_file), "--uninstall", "--dry-run"])
    assert code == 0

    # Uninstall
    code = install_main(["--target", str(target_file), "--uninstall"])
    assert code == 0

    # Install with ccstatusline and dry-run
    code = install_main(["--target", str(target_file), "--use-ccstatusline", "--dry-run"])
    assert code == 0

    # Error handling when corrupted
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("invalid json...")
    code = install_main(["--target", str(target_file)])
    assert code == 1
