# Secrets Scan Design Spec

## Goal
To implement and run a high-performance Python scanner to find any hardcoded credentials, API keys, database connection strings, or private cryptographic keys in the current codebase or in the git commit history of `Calories_Counter_Project`.

## Scope
- **Target Repository**: `/mnt/samsung/Calories_Counter_Project`
- **Active Files Scan**: All files in HEAD, excluding binary files, `.git`, `.venv`, `node_modules`, `db.sqlite3`, and common asset directories.
- **Git History Scan**: Full history (diff patches) across all branches (`git log -p --all`) to catch historical leaks.

## Scan Logic
The scanner will be a self-contained Python script (`scan_secrets.py`) that uses regular expressions and entropy calculations:

### 1. Specific Signature Patterns
- **OpenAI API Key**: `sk-proj-[a-zA-Z0-9]{156}`, `sk-[a-zA-Z0-9]{48}`
- **Google API Key**: `AIzaSy[a-zA-Z0-9\-_]{33}`
- **GitHub Token**: `ghp_[a-zA-Z0-9]{36}`, `github_pat_[a-zA-Z0-9_]{82}`
- **AWS Access Key ID**: `AKIA[0-9A-Z]{16}`
- **AWS Secret Access Key**: `[a-zA-Z0-9/+=]{40}` (when associated with AWS prefix)
- **Private Key**: `-----BEGIN [A-Z ]*PRIVATE KEY-----`
- **Database connection strings**: `(mongodb(?:\+srv)?|postgres|mysql|sqlite|redis|mssql):\/\/[^\s]+`

### 2. High-Entropy Assignment Scanning
Identify potential secrets hardcoded in assignments (e.g. `password = "xyz"`, `secret_key = "abc"`).
- Pattern: `\b(password|passwd|secret|sec|token|api_key|apikey|private_key|auth_token|client_secret|client_id|db_pass|db_password)\b\s*[:=]\s*['"]([^'"]{6,})['"]`
- Filter: Use Shannon entropy to verify if the matched value looks like a randomized secret or a high-entropy string (entropy > 3.0), ignoring standard words/placeholders.

## Safety & Reporting
- The scanner will **mask secrets** in the final report (showing only the first 6 and last 4 characters, e.g. `sk-pro...3Fz1`).
- The report will be generated as a Markdown file: `scan_report.md` in the artifact directory.
- The report will detail:
  - **Active Files findings**: File, line number, matched key name, masked value.
  - **Git History findings**: Commit hash, Author, Date, Commit message, File, line/patch context, matched key name, masked value.
