"""Tests for statusline_bridge module."""

from datetime import datetime, timezone, timedelta
import io
import json
import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.statusline.statusline_bridge import (
    _parse_resets_at,
    main,
    normalize_payload,
    run_bridge,
)


def test_normalize_payload_antigravity_format():
    """Test normalizing a standard Antigravity CLI payload."""
    raw = {
        "modelName": "gemini-2.5-pro",
        "context_window": {
            "total_input_tokens": 50000,
            "total_output_tokens": 1200,
            "max_tokens": 1000000,
            "used_percentage": 5.0,
        },
        "cost": 0.15,
        "workspacePaths": ["/mnt/samsung/Calories_Counter_Project"],
        "rate_limits": {
            "seven_day": {
                "used_percentage": 14.5,
                "resets_in": 3600,
            },
            "block": {
                "resets_in": 300,
            },
        },
        "session_duration": 600,
    }

    normalized = normalize_payload(raw)
    assert normalized["model"] == "gemini-2.5-pro"
    assert normalized["used_tokens"] == 50000
    assert normalized["max_tokens"] == 1000000
    assert normalized["output_tokens"] == 1200
    assert normalized["out"] == 1200
    assert normalized["context_percent"] == 5.0
    assert normalized["cost"] == 0.15
    assert normalized["weekly_percent"] == 14.5
    assert normalized["weekly_reset"] == 3600
    assert normalized["block"] == 300
    assert normalized["session"] == 600
    assert normalized["workspace_dir"] == "/mnt/samsung/Calories_Counter_Project"
    # Auto-resolved git branch should not be None
    assert isinstance(normalized["branch"], str)


def test_normalize_payload_claude_code_format():
    """Test normalizing a standard Claude Code payload."""
    raw = {
        "model": {
            "id": "claude-3-7-sonnet-20250219",
            "display_name": "Claude 3.7 Sonnet",
        },
        "tokens": {
            "input_tokens": 218000,
            "output_tokens": 149200,
        },
        "context_window": {
            "limit": 1000000,
            "used_percentage": 21.8,
        },
        "cost_usd": 12.38,
        "git": {
            "branch": "feature/statusline",
            "is_dirty": True,
            "ahead": 2,
            "behind": 1,
        },
        "workspace": {
            "project_dir": "/custom/path",
        },
        "quota": {
            "weekly_percentage": 25.0,
        },
        "resets_in": 401280,
        "elapsed_time": 1740,
        "hints": "shift+tab to cycle",
    }

    normalized = normalize_payload(raw)
    assert normalized["model"] == "Claude 3.7 Sonnet"
    assert normalized["used_tokens"] == 218000
    assert normalized["max_tokens"] == 1000000
    assert normalized["output_tokens"] == 149200
    assert normalized["out"] == 149200
    assert normalized["context_percent"] == 21.8
    assert normalized["cost"] == 12.38
    assert normalized["branch"] == "feature/statusline"
    assert normalized["is_dirty"] is True
    assert normalized["ahead"] == 2
    assert normalized["behind"] == 1
    assert normalized["weekly_percent"] == 25.0
    assert normalized["weekly_reset"] == 401280
    assert normalized["session"] == 1740
    assert normalized["hints"] == "shift+tab to cycle"
    assert normalized["workspace_dir"] == "/custom/path"


def test_normalize_payload_empty_and_defaults():
    """Test default values when empty payload is given."""
    normalized = normalize_payload({})
    assert normalized["model"] in ("Gemini 3.7 Flash", "Auto")
    assert normalized["used_tokens"] == 0
    assert normalized["max_tokens"] == 1000000
    assert normalized["output_tokens"] == 0
    assert normalized["cost"] == 0.0
    assert normalized["context_percent"] == 0.0
    assert normalized["weekly_percent"] == 0.0
    assert isinstance(normalized["branch"], str)


def test_normalize_payload_non_dict():
    """Test normalize_payload when non-dict is passed."""
    normalized = normalize_payload(None)  # type: ignore
    assert normalized["model"] == "Gemini 3.7 Flash"
    assert normalized["used_tokens"] == 0


def test_normalize_payload_model_variations():
    """Test various model name input formats."""
    # String model
    res1 = normalize_payload({"model": "claude-3-opus"})
    assert res1["model"] == "claude-3-opus"

    # Dict model with id only
    res2 = normalize_payload({"model": {"id": "claude-3-5-haiku"}})
    assert res2["model"] == "claude-3-5-haiku"

    # Dict model with display_name
    res3 = normalize_payload({"model": {"id": "claude-3-5", "display_name": "Claude 3.5 Sonnet"}})
    assert res3["model"] == "Claude 3.5 Sonnet"

    # model_name field
    res4 = normalize_payload({"model_name": "gemini-flash"})
    assert res4["model"] == "gemini-flash"

    # None or empty
    res5 = normalize_payload({"model": ""})
    assert res5["model"] == "Gemini 3.7 Flash"


def test_normalize_payload_token_and_cost_aliases():
    """Test various field aliases for tokens, cost, rate limits."""
    raw = {
        "tokens_used": 15000,
        "tokens_out": 2500,
        "context_max": 500000,
        "spend": 3.45,
        "weekly": 45.0,
        "weekly_reset_seconds": 12000,
        "block_seconds": 1800,
        "session_seconds": 3600,
    }
    normalized = normalize_payload(raw)
    assert normalized["used_tokens"] == 15000
    assert normalized["output_tokens"] == 2500
    assert normalized["max_tokens"] == 500000
    assert normalized["cost"] == 3.45
    assert normalized["context_percent"] == 3.0  # 15000 / 500000 * 100
    assert normalized["weekly_percent"] == 45.0
    assert normalized["weekly_reset"] == 12000
    assert normalized["block"] == 1800
    assert normalized["session"] == 3600


def test_normalize_payload_nested_cost_dict():
    """Test cost specified as a dictionary."""
    raw = {"cost": {"total_cost_usd": 8.75}}
    normalized = normalize_payload(raw)
    assert normalized["cost"] == 8.75


def test_normalize_payload_workspace_variations():
    """Test various workspace path resolutions."""
    # cwd parameter overrides
    n1 = normalize_payload({"workspacePaths": ["/p1"]}, cwd="/override")
    assert n1["workspace_dir"] == "/override"

    # workspace.path
    n2 = normalize_payload({"workspace": {"path": "/path/two"}})
    assert n2["workspace_dir"] == "/path/two"

    # workspace_path top-level
    n3 = normalize_payload({"workspace_path": "/path/three"})
    assert n3["workspace_dir"] == "/path/three"


def test_normalize_payload_context_percentage_calculation():
    """Test context percent calculation when not explicitly provided."""
    raw = {
        "used_tokens": 250000,
        "max_tokens": 1000000,
    }
    normalized = normalize_payload(raw)
    assert normalized["context_percent"] == 25.0

    raw_zero = {
        "used_tokens": 0,
        "max_tokens": 1000000,
    }
    assert normalize_payload(raw_zero)["context_percent"] == 0.0


def test_parse_resets_at():
    """Test parsing various datetime and second formats."""
    assert _parse_resets_at(None) is None
    assert _parse_resets_at(123) == 123
    assert _parse_resets_at(456.7) == 456
    assert _parse_resets_at("789") == 789

    # Future ISO datetime
    future_dt = datetime.now(timezone.utc) + timedelta(seconds=3600)
    iso_val = future_dt.isoformat().replace("+00:00", "Z")
    parsed_secs = _parse_resets_at(iso_val)
    assert parsed_secs is not None
    assert 3590 <= parsed_secs <= 3610

    # Invalid string
    assert _parse_resets_at("not-a-date") is None


def test_normalize_payload_git_auto_resolution():
    """Test automatic git resolution via git_info module when branch is missing."""
    mock_git_status = {
        "branch": "auto-branch-test",
        "is_dirty": True,
        "ahead": 3,
        "behind": 0,
        "detached": False,
    }

    with patch("scripts.statusline.statusline_bridge.get_git_status", return_value=mock_git_status) as mock_fn:
        normalized = normalize_payload({"cwd": "/mock/dir"})
        mock_fn.assert_called_once_with("/mock/dir")
        assert normalized["branch"] == "auto-branch-test"
        assert normalized["is_dirty"] is True
        assert normalized["ahead"] == 3
        assert normalized["behind"] == 0


def test_normalize_payload_git_explicit_preserved():
    """Test that explicit git branch in payload is preserved without git_info call."""
    with patch("scripts.statusline.statusline_bridge.get_git_status") as mock_fn:
        normalized = normalize_payload({"branch": "explicit-branch", "cwd": "/mock/dir"})
        mock_fn.assert_not_called()
        assert normalized["branch"] == "explicit-branch"


def test_run_bridge_force_native():
    """Test run_bridge directly calling native_renderer."""
    payload = {
        "model": "test-model",
        "used_tokens": 100,
        "max_tokens": 1000,
        "cost": 1.0,
        "branch": "main",
    }
    rendered = run_bridge(payload, force_native=True)
    assert "Model: test-model" in rendered
    assert "Cost: $1.00" in rendered
    assert "⤹ main" in rendered


def test_run_bridge_ccstatusline_success():
    """Test run_bridge when ccstatusline succeeds."""
    mock_stdout = "CUSTOM CCSTATUSLINE OUTPUT\nLINE 2\nLINE 3\n"
    mock_proc = MagicMock(returncode=0, stdout=mock_stdout, stderr="")

    with patch("subprocess.run", return_value=mock_proc):
        output = run_bridge({"model": "test"}, use_ccstatusline=True)
        assert output == "CUSTOM CCSTATUSLINE OUTPUT\nLINE 2\nLINE 3"


def test_run_bridge_ccstatusline_npx_fallback():
    """Test run_bridge trying npx fallback when ccstatusline binary is not found."""
    mock_proc = MagicMock(returncode=0, stdout="NPX CCSTATUSLINE OUTPUT\n", stderr="")

    def side_effect(cmd, **kwargs):
        if cmd == ["ccstatusline"]:
            raise FileNotFoundError("ccstatusline not found")
        elif cmd == ["npx", "--no-install", "ccstatusline"]:
            return mock_proc
        raise FileNotFoundError()

    with patch("subprocess.run", side_effect=side_effect):
        output = run_bridge({"model": "test"}, use_ccstatusline=True)
        assert output == "NPX CCSTATUSLINE OUTPUT"


def test_run_bridge_ccstatusline_fallback_on_filenotfound():
    """Test run_bridge falling back to native renderer when ccstatusline is not found."""
    with patch("subprocess.run", side_effect=FileNotFoundError("ccstatusline not found")):
        output = run_bridge({"model": "fallback-test"}, use_ccstatusline=True)
        assert "Model: fallback-test" in output


def test_run_bridge_ccstatusline_fallback_on_timeout():
    """Test run_bridge falling back to native renderer when ccstatusline times out."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ccstatusline", timeout=0.3)):
        output = run_bridge({"model": "timeout-test"}, use_ccstatusline=True)
        assert "Model: timeout-test" in output


def test_run_bridge_ccstatusline_fallback_on_error_code():
    """Test run_bridge falling back to native renderer when ccstatusline exits non-zero."""
    mock_proc = MagicMock(returncode=1, stdout="", stderr="error")
    with patch("subprocess.run", return_value=mock_proc):
        output = run_bridge({"model": "error-test"}, use_ccstatusline=True)
        assert "Model: error-test" in output


def test_main_cli_function(monkeypatch, capsys):
    """Test main() entrypoint using mock CLI arguments."""
    test_args = ["statusline_bridge.py", "--sample", "--json"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["model"] == "gemini-2.5-pro"
    assert parsed["cost"] == 12.38


def test_main_cli_function_native(monkeypatch, capsys):
    """Test main() with --sample and --no-color."""
    test_args = ["statusline_bridge.py", "--sample", "--no-color"]
    monkeypatch.setattr(sys, "argv", test_args)
    main()
    captured = capsys.readouterr()
    assert "Model: gemini-2.5-pro" in captured.out
    assert "\033[" not in captured.out


def test_cli_sample_flag():
    """Test CLI with --sample flag."""
    cmd = [sys.executable, "scripts/statusline/statusline_bridge.py", "--sample"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2.0)
    assert res.returncode == 0
    assert "Model:" in res.stdout
    assert "Context:" in res.stdout
    assert "Cost:" in res.stdout


def test_cli_sample_json_flag():
    """Test CLI with --sample --json flags outputting valid JSON."""
    cmd = [sys.executable, "scripts/statusline/statusline_bridge.py", "--sample", "--json"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2.0)
    assert res.returncode == 0
    parsed = json.loads(res.stdout)
    assert "model" in parsed
    assert "used_tokens" in parsed
    assert "cost" in parsed
    assert "branch" in parsed


def test_cli_stdin_pipe():
    """Test piping JSON into CLI stdin."""
    payload = json.dumps({"modelName": "custom-cli-model", "cost": 4.56, "branch": "cli-branch"})
    cmd = [sys.executable, "scripts/statusline/statusline_bridge.py", "--native"]
    res = subprocess.run(cmd, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2.0)
    assert res.returncode == 0
    assert "Model: custom-cli-model" in res.stdout
    assert "Cost: $4.56" in res.stdout
    assert "cli-branch" in res.stdout


def test_cli_empty_stdin_graceful_fallback():
    """Test empty stdin doesn't crash and returns exit code 0."""
    cmd = [sys.executable, "scripts/statusline/statusline_bridge.py"]
    res = subprocess.run(cmd, input="", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2.0)
    assert res.returncode == 0
    assert "Model:" in res.stdout


def test_cli_malformed_stdin_graceful_fallback():
    """Test malformed JSON stdin doesn't crash and returns exit code 0."""
    cmd = [sys.executable, "scripts/statusline/statusline_bridge.py"]
    res = subprocess.run(cmd, input="{invalid json...", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2.0)
    assert res.returncode == 0
    assert "Model:" in res.stdout


def test_cli_positional_json_argument():
    """Test passing JSON string as positional argument."""
    arg = json.dumps({"model": "positional-model", "cost": 7.89})
    cmd = [sys.executable, "scripts/statusline/statusline_bridge.py", arg, "--json"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2.0)
    assert res.returncode == 0
    parsed = json.loads(res.stdout)
    assert parsed["model"] == "positional-model"
    assert parsed["cost"] == 7.89
