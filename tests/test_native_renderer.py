import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.statusline.native_renderer import (
    format_tokens,
    render_progress_bar,
    format_duration,
    strip_ansi,
    render_statusline,
)


# ============================================================================
# format_tokens tests
# ============================================================================

def test_format_tokens_zero_and_small():
    assert format_tokens(0) == "0"
    assert format_tokens(500) == "500"
    assert format_tokens(999) == "999"


def test_format_tokens_thousands():
    assert format_tokens(1000) == "1k"
    assert format_tokens(1500) == "1.5k"
    assert format_tokens(149200) == "149.2k"
    assert format_tokens(218000) == "218k"


def test_format_tokens_millions():
    assert format_tokens(1000000) == "1.0M"
    assert format_tokens(1500000) == "1.5M"
    assert format_tokens(2000000) == "2.0M"


def test_format_tokens_none_and_negative():
    assert format_tokens(None) == "0"
    assert format_tokens(-100) == "0"


# ============================================================================
# render_progress_bar tests
# ============================================================================

def test_render_progress_bar_empty():
    bar = render_progress_bar(0.0, width=8)
    assert bar == "        "
    assert len(bar) == 8


def test_render_progress_bar_full():
    bar = render_progress_bar(100.0, width=8)
    assert bar == "████████"
    assert len(bar) == 8


def test_render_progress_bar_half():
    bar = render_progress_bar(50.0, width=8)
    assert bar == "████    "
    assert len(bar) == 8


def test_render_progress_bar_partial():
    bar = render_progress_bar(22.0, width=8)
    assert bar == "██      "
    assert len(bar) == 8


def test_render_progress_bar_custom_width():
    assert render_progress_bar(50.0, width=4) == "██  "
    assert render_progress_bar(0.0, width=4) == "    "
    assert render_progress_bar(100.0, width=4) == "████"


def test_render_progress_bar_bounds():
    assert render_progress_bar(-10.0, width=8) == "        "
    assert render_progress_bar(120.0, width=8) == "████████"


# ============================================================================
# format_duration tests
# ============================================================================

def test_format_duration_minutes():
    assert format_duration(1740) == "29m"
    assert format_duration(60) == "1m"
    assert format_duration(0) == "0m"
    assert format_duration(-10) == "0m"
    assert format_duration(None) == "0m"


def test_format_duration_hours():
    assert format_duration(3600) == "1hr 0m"
    assert format_duration(9660) == "2hr 41m"


def test_format_duration_days():
    assert format_duration(86400) == "1d 0hr 0m"
    assert format_duration(399600) == "4d 15hr 0m"
    # 4d 15hr 28m = 4*86400 + 15*3600 + 28*60 = 345600 + 54000 + 1680 = 401280
    assert format_duration(401280) == "4d 15hr 28m"


# ============================================================================
# strip_ansi tests
# ============================================================================

def test_strip_ansi_plain_text():
    assert strip_ansi("hello world") == "hello world"


def test_strip_ansi_colored_text():
    colored = "\033[36mModel: Claude\033[0m | \033[32mCost: $12.38\033[0m"
    assert strip_ansi(colored) == "Model: Claude | Cost: $12.38"


def test_strip_ansi_nested_and_bright():
    colored = "\033[91m❯❯\033[0m\033[90m | \033[35m⤹ main\033[0m"
    assert strip_ansi(colored) == "❯❯ | ⤹ main"


# ============================================================================
# render_statusline tests
# ============================================================================

@pytest.fixture
def sample_status_data():
    return {
        "model": "claude-3.7-sonnet",
        "used_tokens": 218000,
        "max_tokens": 1000000,
        "context_percent": 22.0,
        "cost": 12.38,
        "branch": "main",
        "weekly_percent": 20.0,
        "weekly_reset": 401280,  # 4d 15hr 28m
        "block": 9660,  # 2hr 41m
        "session": 1740,  # 29m
        "out": 149200,  # 149.2k
    }


def test_render_statusline_three_lines(sample_status_data):
    result = render_statusline(sample_status_data, enable_color=False)
    lines = result.splitlines()
    assert len(lines) == 3


def test_render_statusline_line1_content(sample_status_data):
    result = render_statusline(sample_status_data, enable_color=False)
    lines = result.splitlines()
    line1 = lines[0]

    assert "Model: claude-3.7-sonnet" in line1
    assert "Context: [██      ] 218k/1.0M (22%)" in line1
    assert "Cost: $12.38" in line1
    assert "⤹ main" in line1


def test_render_statusline_line2_content(sample_status_data):
    result = render_statusline(sample_status_data, enable_color=False)
    lines = result.splitlines()
    line2 = lines[1]

    assert "Weekly: 20.0%" in line2
    assert "Weekly Reset: 4d 15hr 28m" in line2
    assert "Block: 2hr 41m" in line2
    assert "Session: 29m" in line2
    assert "Out: 149.2k" in line2


def test_render_statusline_line3_content(sample_status_data):
    result = render_statusline(sample_status_data, enable_color=False)
    lines = result.splitlines()
    line3 = lines[2]

    assert line3.startswith("❯❯")
    assert "bypass permissions on (shift+tab to cycle)" in line3
    assert "install gh for PR status" in line3
    assert "← for agents" in line3


def test_render_statusline_strip_ansi_matches_no_color(sample_status_data):
    colored = render_statusline(sample_status_data, enable_color=True)
    plain = render_statusline(sample_status_data, enable_color=False)
    assert strip_ansi(colored) == plain


def test_render_statusline_branch_truncation():
    data = {
        "model": "claude-3.7-sonnet",
        "branch": "feature/very-long-branch-name-here",
    }
    result = render_statusline(data, enable_color=False)
    lines = result.splitlines()
    # Branch is longer than 15 chars, truncated to 15 with ellipsis: feature/very...
    assert "⤹ feature/very..." in lines[0]


def test_render_statusline_branch_short_no_truncation():
    data = {
        "model": "claude-3.7-sonnet",
        "branch": "short-branch",
    }
    result = render_statusline(data, enable_color=False)
    lines = result.splitlines()
    assert "⤹ short-branch" in lines[0]


def test_render_statusline_empty_data_fallback():
    result = render_statusline({}, enable_color=False)
    lines = result.splitlines()
    assert len(lines) == 3
    assert "Model:" in lines[0]
    assert "Cost: $0.00" in lines[0]
    assert "Weekly: 0.0%" in lines[1]
    assert "Session: 0m" in lines[1]
    assert "Out: 0" in lines[1]
    assert lines[2].startswith("❯❯")


def test_render_statusline_context_bar_colors():
    # Green for < 50%
    data_green = {"context_percent": 30.0}
    colored_green = render_statusline(data_green, enable_color=True)
    assert "\033[32m" in colored_green  # Green

    # Yellow for 50-80%
    data_yellow = {"context_percent": 65.0}
    colored_yellow = render_statusline(data_yellow, enable_color=True)
    assert "\033[33m" in colored_yellow  # Yellow

    # Red for > 80%
    data_red = {"context_percent": 85.0}
    colored_red = render_statusline(data_red, enable_color=True)
    assert "\033[31m" in colored_red  # Red


def test_render_statusline_custom_hints():
    data = {"hints": "custom mode hint · help"}
    result = render_statusline(data, enable_color=False)
    lines = result.splitlines()
    assert lines[2] == "❯❯ custom mode hint · help"


def test_render_statusline_ansi_colors_present():
    data = {
        "model": "claude",
        "cost": 5.0,
        "branch": "main",
        "weekly_percent": 15.0,
    }
    colored = render_statusline(data, enable_color=True)
    assert "\033[36m" in colored  # Cyan for model
    assert "\033[90m" in colored  # Gray separator
    assert "\033[32m" in colored  # Green cost
    assert "\033[35m" in colored  # Magenta branch
    assert "\033[94m" in colored  # Bright blue weekly
    assert "\033[91m" in colored  # Red/coral marker


def test_render_statusline_nested_data():
    data = {
        "model": "claude-3.7-sonnet",
        "context": {"used": 150000, "max": 200000, "percent": 75.0},
        "git": {"branch": "dev-branch"},
    }
    result = render_statusline(data, enable_color=False)
    lines = result.splitlines()
    assert "Context: [██████  ] 150k/200k (75%)" in lines[0]
    assert "⤹ dev-branch" in lines[0]


def test_cli_execution_default():
    import subprocess
    script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "scripts", "statusline", "native_renderer.py")
    )
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=True)
    assert "Model: claude-3.7-sonnet" in result.stdout
    assert "Weekly: 20.0%" in result.stdout


def test_cli_execution_with_json_arg():
    import subprocess
    import json
    script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "scripts", "statusline", "native_renderer.py")
    )
    payload = json.dumps({"model": "gpt-4o", "cost": 1.25, "branch": "fix/test"})
    result = subprocess.run([sys.executable, script_path, payload], capture_output=True, text=True, check=True)
    assert "Model: gpt-4o" in result.stdout
    assert "Cost: $1.25" in result.stdout
    assert "⤹ fix/test" in result.stdout


def test_cli_execution_with_stdin():
    import subprocess
    import json
    script_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "scripts", "statusline", "native_renderer.py")
    )
    payload = json.dumps({"model": "custom-model", "cost": 0.05})
    result = subprocess.run(
        [sys.executable, script_path],
        input=payload,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Model: custom-model" in result.stdout
    assert "Cost: $0.05" in result.stdout

