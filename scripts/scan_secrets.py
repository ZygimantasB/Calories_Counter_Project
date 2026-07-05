import re

PATTERNS = {
    'OpenAI API Key': r'sk-proj-[a-zA-Z0-9]{156}|sk-[a-zA-Z0-9]{48}',
    'Google API Key': r'AIzaSy[a-zA-Z0-9\-_]{33}',
    'GitHub Token': r'ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82}',
    'AWS Access Key ID': r'AKIA[0-9A-Z]{16}',
    'Private Key': r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    'Database Connection': r'(mongodb(?:\+srv)?|postgresql|postgres|mysql|sqlite|redis|mssql):\/\/[^\s\'"]+'
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
