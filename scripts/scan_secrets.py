import re

PATTERNS = {
    'OpenAI API Key': r'\b(?:sk-proj-[a-zA-Z0-9]{156}|sk-[a-zA-Z0-9]{48})\b',
    'Google API Key': r'\bAIzaSy[a-zA-Z0-9\-_]{33}\b',
    'GitHub Token': r'\b(?:ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})\b',
    'AWS Access Key ID': r'\b(A[SK]IA)[0-9A-Z]{16}\b',
    'Private Key': r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    'Database Connection': r'(?i)\b(mongodb(?:\+srv)?|postgresql|postgres|mysql|sqlite|redis|mssql|mariadb):\/\/[^\s\'"]+'
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
