# Secrets Scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a standalone Python-based secrets scanner to check the active codebase and git commit history of `Calories_Counter_Project` for credentials, API keys, private keys, and database connection strings, generating a clean Markdown report with masked findings.

**Architecture:**
The scanner will consist of a main script `scripts/scan_secrets.py` containing modular regex scanners, an entropy calculator for variable assignments, a file walker, and a git log parser. Testing will be implemented using Python's standard `unittest` library in `tests/test_scan_secrets.py`.

**Architecture Diagram:**
```mermaid
graph TD
    subgraph "Secrets Scanner"
        main["scripts/scan_secrets.py"] --> signature["Signature Matcher"]
        main --> entropy["Entropy Checker"]
        main --> active_scanner["Active Files Walker"]
        main --> git_scanner["Git History Scanner"]
        main --> reporter["Markdown Reporter"]
    end
    subgraph "Testing"
        tests["tests/test_scan_secrets.py"] --> main
    end
```

**Tech Stack:** Python 3 (standard libraries: `re`, `subprocess`, `math`, `os`, `unittest`)

## Global Constraints
- Target workspace: `/mnt/samsung/Calories_Counter_Project`
- Output report path: `/home/zygimantas/.gemini/antigravity-cli/brain/3a0e85b3-1b54-4d4f-ac94-309e494028fe/scan_report.md`
- Masking requirement: Secret values must be masked (showing only the first 6 and last 4 characters, e.g., `sk-pro...3Fz1`) in all output logs and report.
- TDD process for each task: write failing test, verify failure, implement code, verify pass, commit.

---

### Task 1: Signature Matching Engines

**Files:**
- Create: `scripts/scan_secrets.py`
- Create: `tests/test_scan_secrets.py`

**Interfaces:**
- Consumes: None
- Produces: `scan_text(text: str) -> list[dict]` returns a list of dictionaries with keys `type` and `matched_value`.

- [ ] **Step 1: Write the failing tests for signature matching**
Create `tests/test_scan_secrets.py`:
```python
import unittest
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from scan_secrets import scan_text

class TestSecretsMatcher(unittest.TestCase):
    def test_openai_key(self):
        text = "openai_key = 'sk-proj-1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz'"
        results = scan_text(text)
        self.assertTrue(any(r['type'] == 'OpenAI API Key' for r in results))

    def test_google_key(self):
        text = "google_key = 'AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q'"
        results = scan_text(text)
        self.assertTrue(any(r['type'] == 'Google API Key' for r in results))

    def test_private_key(self):
        text = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQD\n-----END PRIVATE KEY-----"
        results = scan_text(text)
        self.assertTrue(any(r['type'] == 'Private Key' for r in results))

    def test_db_connection(self):
        text = "db = 'postgresql://user:pass@localhost:5432/db'"
        results = scan_text(text)
        self.assertTrue(any(r['type'] == 'Database Connection' for r in results))

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: FAIL/Error (ModuleNotFoundError: No module named 'scan_secrets')

- [ ] **Step 3: Write minimal implementation**
Create `scripts/scan_secrets.py`:
```python
import re

PATTERNS = {
    'OpenAI API Key': r'sk-proj-[a-zA-Z0-9]{156}|sk-[a-zA-Z0-9]{48}',
    'Google API Key': r'AIzaSy[a-zA-Z0-9\-_]{33}',
    'GitHub Token': r'ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82}',
    'AWS Access Key ID': r'AKIA[0-9A-Z]{16}',
    'Private Key': r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    'Database Connection': r'(mongodb(?:\+srv)?|postgres|mysql|sqlite|redis|mssql):\/\/[^\s\'"]+'
}

def scan_text(text: str) -> list[dict]:
    findings = []
    for name, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text):
            findings.append({
                'type': name,
                'matched_value': match.group(0)
            })
    return findings
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add scripts/scan_secrets.py tests/test_scan_secrets.py
git commit -m "test(scanner): implement signature matching and tests"
```

---

### Task 2: Entropy Calculator & Assignment Scanning

**Files:**
- Modify: `scripts/scan_secrets.py`
- Modify: `tests/test_scan_secrets.py`

**Interfaces:**
- Consumes: `scan_text(text: str) -> list[dict]` from Task 1
- Produces: 
  - `calculate_entropy(text: str) -> float`
  - `scan_text_entropy(text: str) -> list[dict]` returns variable assignment findings with high entropy.

- [ ] **Step 1: Write the failing tests**
Modify `tests/test_scan_secrets.py`:
```python
    def test_entropy_high(self):
        from scan_secrets import calculate_entropy
        # Random password string has high entropy
        self.assertGreater(calculate_entropy("f48h2ndK#9a!df"), 3.0)
        # Normal words have low entropy
        self.assertLess(calculate_entropy("password"), 3.0)

    def test_assignment_scanner(self):
        from scan_secrets import scan_text_entropy
        text = "db_password = 'rAnd0m#StRiNg!LeAk'"
        results = scan_text_entropy(text)
        self.assertTrue(any(r['type'] == 'Potential Secret Assignment' for r in results))
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: FAIL (AttributeError: module 'scan_secrets' has no attribute 'scan_text_entropy')

- [ ] **Step 3: Write minimal implementation**
Modify `scripts/scan_secrets.py`:
```python
import math

def calculate_entropy(text: str) -> float:
    if not text:
        return 0.0
    entropy = 0.0
    for char in set(text):
        p_x = text.count(char) / len(text)
        entropy += - p_x * math.log2(p_x)
    return entropy

ASSIGNMENT_PATTERN = r'\b(password|passwd|secret|sec|token|api_key|apikey|private_key|auth_token|client_secret|client_id|db_pass|db_password)\b\s*[:=]\s*[\'"]([^\'"]{6,})[\'"]'

def scan_text_entropy(text: str) -> list[dict]:
    findings = []
    # Regular matching
    findings.extend(scan_text(text))
    # Entropy matching
    for match in re.finditer(ASSIGNMENT_PATTERN, text, re.IGNORECASE):
        var_name = match.group(1)
        val = match.group(2)
        # Skip obvious placeholders/dummy values
        if any(dummy in val.lower() for dummy in ['placeholder', 'example', 'your_password', 'secret_here', 'dummy', 'template', 'my_password']):
            continue
        entropy = calculate_entropy(val)
        if entropy > 3.0:
            findings.append({
                'type': 'Potential Secret Assignment',
                'matched_value': val,
                'variable': var_name
            })
    return findings
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add scripts/scan_secrets.py tests/test_scan_secrets.py
git commit -m "feat(scanner): add entropy scanning for variable assignments"
```

---

### Task 3: Active Files Scan (HEAD)

**Files:**
- Modify: `scripts/scan_secrets.py`
- Modify: `tests/test_scan_secrets.py`

**Interfaces:**
- Consumes: `scan_text_entropy(text: str) -> list[dict]`
- Produces: `scan_active_files(root_dir: str) -> list[dict]` where each entry contains `file_path`, `line_number`, `type`, `matched_value`, `variable` (optional).

- [ ] **Step 1: Write the failing tests**
Modify `tests/test_scan_secrets.py`:
```python
    def test_scan_active_files(self):
        from scan_secrets import scan_active_files
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        try:
            # Create a file with a secret
            secret_file = os.path.join(temp_dir, "config.py")
            with open(secret_file, "w") as f:
                f.write("db_password = 's3cr3t#Pa$$word!'\n")
            
            # Create a binary/ignored file or node_modules
            ignored_dir = os.path.join(temp_dir, "node_modules")
            os.makedirs(ignored_dir)
            with open(os.path.join(ignored_dir, "test.js"), "w") as f:
                f.write("password = 's3cr3t#Pa$$word!'\n")

            results = scan_active_files(temp_dir)
            # Should find secret in config.py, but not node_modules
            self.assertTrue(any("config.py" in r['file_path'] for r in results))
            self.assertFalse(any("node_modules" in r['file_path'] for r in results))
        finally:
            shutil.rmtree(temp_dir)
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: FAIL (ImportError: cannot import name 'scan_active_files')

- [ ] **Step 3: Write minimal implementation**
Modify `scripts/scan_secrets.py`:
```python
import os

EXCLUDED_DIRS = {
    '.git', '.venv', 'node_modules', '.idea', '__pycache__', 
    'venv', 'env', 'dist', 'build', '.ai', '.claude', '.superpowers', '.remember', 'qa_screenshots', 'test-results', 'static'
}
EXCLUDED_FILES = {
    'db.sqlite3', 'db_backup.sqlite3', 'uv.lock', 'package-lock.json', 'db.sqlite3.bak-20260704-164609'
}
BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz', '.db', '.sqlite3', '.sqlite'
}

def scan_active_files(root_dir: str) -> list[dict]:
    findings = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude directories in-place
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        
        for filename in filenames:
            if filename in EXCLUDED_FILES:
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext in BINARY_EXTENSIONS:
                continue
                
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        secrets = scan_text_entropy(line)
                        for secret in secrets:
                            findings.append({
                                'file_path': os.path.relpath(file_path, root_dir),
                                'line_number': line_num,
                                'type': secret['type'],
                                'matched_value': secret['matched_value'],
                                'variable': secret.get('variable')
                            })
            except Exception:
                pass # skip unreadable files
    return findings
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add scripts/scan_secrets.py tests/test_scan_secrets.py
git commit -m "feat(scanner): implement active file scanning"
```

---

### Task 4: Git History Scan

**Files:**
- Modify: `scripts/scan_secrets.py`
- Modify: `tests/test_scan_secrets.py`

**Interfaces:**
- Consumes: `scan_text_entropy(text: str) -> list[dict]`
- Produces: `scan_git_history(root_dir: str) -> list[dict]` returning commit metadata, file, line content, and findings.

- [ ] **Step 1: Write the failing tests**
Modify `tests/test_scan_secrets.py`:
```python
    def test_scan_git_history(self):
        from scan_secrets import scan_git_history
        # Test scan_git_history using mock git output behavior or mock subprocess
        # We can mock subprocess.check_output to return a sample diff with secrets
        from unittest.mock import patch
        
        mock_git_output = b"""commit c1b2a3f4e5d6
Author: Test User <test@example.com>
Date:   Sun Jul 5 12:00:00 2026 -0400

    feat: add db connection

diff --git a/config.py b/config.py
index 1234567..7890abc 100644
--- a/config.py
+++ b/config.py
@@ -1,3 +1,4 @@
+db_url = 'postgres://admin:supersecret@localhost:5432/main'
"""
        with patch('subprocess.check_output', return_value=mock_git_output):
            results = scan_git_history('/dummy/dir')
            self.assertTrue(any(r['commit'] == 'c1b2a3f4e5d6' for r in results))
            self.assertTrue(any('supersecret' in r['matched_value'] for r in results))
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: FAIL (ImportError: cannot import name 'scan_git_history')

- [ ] **Step 3: Write minimal implementation**
Modify `scripts/scan_secrets.py`:
```python
import subprocess

def scan_git_history(root_dir: str) -> list[dict]:
    findings = []
    try:
        # Run git log with full patches for all commits
        cmd = ['git', 'log', '-p', '--all']
        # Set environment to handle possible encoding issues
        env = os.environ.copy()
        env['PAGER'] = 'cat'
        
        output = subprocess.check_output(cmd, cwd=root_dir, env=env).decode('utf-8', errors='ignore')
        
        current_commit = None
        current_author = None
        current_date = None
        current_message = []
        current_file = None
        in_message = False
        
        lines = output.split('\n')
        for line in lines:
            if line.startswith('commit '):
                current_commit = line.split(' ')[1]
                current_author = None
                current_date = None
                current_message = []
                current_file = None
                in_message = False
                continue
            
            if line.startswith('Author: '):
                current_author = line[8:].strip()
                continue
                
            if line.startswith('Date:   '):
                current_date = line[8:].strip()
                in_message = True
                continue
                
            if in_message:
                if line.startswith('    '):
                    current_message.append(line.strip())
                    continue
                else:
                    in_message = False
            
            if line.startswith('diff --git '):
                # Extract file name
                parts = line.split(' ')
                if len(parts) >= 4:
                    current_file = parts[3].replace('b/', '', 1)
                continue
            
            # Check added lines (starts with '+', but not '+++')
            if line.startswith('+') and not line.startswith('+++'):
                added_content = line[1:]
                secrets = scan_text_entropy(added_content)
                for secret in secrets:
                    findings.append({
                        'commit': current_commit,
                        'author': current_author,
                        'date': current_date,
                        'message': ' '.join(current_message),
                        'file_path': current_file,
                        'matched_value': secret['matched_value'],
                        'type': secret['type']
                    })
    except Exception as e:
        # If not a git repo or git is not installed, return empty
        pass
    return findings
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add scripts/scan_secrets.py tests/test_scan_secrets.py
git commit -m "feat(scanner): implement git history scanning"
```

---

### Task 5: Reporter, Masking, and Script Wrapper

**Files:**
- Modify: `scripts/scan_secrets.py`
- Modify: `tests/test_scan_secrets.py`

**Interfaces:**
- Consumes: `scan_active_files(root_dir: str)`, `scan_git_history(root_dir: str)`
- Produces: Command Line Interface running both scans and outputting masked report to the requested target file.

- [ ] **Step 1: Write the failing tests for masking**
Modify `tests/test_scan_secrets.py`:
```python
    def test_mask_secret(self):
        from scan_secrets import mask_secret
        self.assertEqual(mask_secret("1234567890"), "123456...7890")
        self.assertEqual(mask_secret("abc"), "***")
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: FAIL (ImportError: cannot import name 'mask_secret')

- [ ] **Step 3: Write minimal implementation**
Modify `scripts/scan_secrets.py`:
```python
def mask_secret(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 8:
        return "***"
    return f"{secret[:6]}...{secret[-4:]}"

def generate_report(active_findings: list[dict], git_findings: list[dict], report_path: str):
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Secrets Scanner Findings Report\n\n")
        f.write(f"Report generated on: {os.popen('date').read().strip()}\n\n")
        
        f.write("## Summary\n")
        f.write(f"- Active codebase findings: **{len(active_findings)}**\n")
        f.write(f"- Git history findings: **{len(git_findings)}**\n\n")
        
        f.write("## Active Codebase Findings\n")
        if not active_findings:
            f.write("No secrets found in current codebase files.\n\n")
        else:
            f.write("| File | Line | Type | Variable | Masked Secret |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            for r in active_findings:
                var = r.get('variable') or '-'
                f.write(f"| {r['file_path']} | {r['line_number']} | {r['type']} | {var} | `{mask_secret(r['matched_value'])}` |\n")
            f.write("\n")
            
        f.write("## Git History Findings\n")
        if not git_findings:
            f.write("No secrets found in git history.\n\n")
        else:
            f.write("| Commit | Author | Date | File | Type | Masked Secret | Message |\n")
            f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
            for r in git_findings:
                commit_short = r['commit'][:8] if r['commit'] else '-'
                f.write(f"| `{commit_short}` | {r['author']} | {r['date']} | {r['file_path']} | {r['type']} | `{mask_secret(r['matched_value'])}` | {r['message']} |\n")
            f.write("\n")

if __name__ == '__main__':
    import sys
    root = "/mnt/samsung/Calories_Counter_Project"
    out = "/home/zygimantas/.gemini/antigravity-cli/brain/3a0e85b3-1b54-4d4f-ac94-309e494028fe/scan_report.md"
    
    print("Scanning active codebase files...")
    act = scan_active_files(root)
    
    print("Scanning git history...")
    git_f = scan_git_history(root)
    
    print(f"Generating report at {out}...")
    generate_report(act, git_f, out)
    print("Done!")
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_scan_secrets.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add scripts/scan_secrets.py tests/test_scan_secrets.py
git commit -m "feat(scanner): implement markdown reporter, secret masking, and script CLI wrapper"
```
