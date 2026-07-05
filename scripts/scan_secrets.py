import re
import math

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
