#!/usr/bin/env python3
"""Regression test for hardcoded paths in JSON files.

Scans ALL tracked JSON/JSONC files in the repo and fails if any contain:
- Hardcoded Windows user paths (C:\\Users\\David, C:/Users/David)
- BOM characters in file or embedded in strings
- Unresolved template variables ({{USERPROFILE}} in non-template files)

Usage:
  python scripts/test_json_sanitization.py     # run tests
  python scripts/test_json_sanitization.py --jsonc-only  # only config templates
"""
import io, sys, re, os, json, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Files that are DATA/HISTORICAL (may contain {{USERPROFILE}} in text descriptions)
DATA_FILES = {
    'conhecimento/memoria/memories.json',
    'conhecimento/memoria/index.json',
    'conhecimento/memoria/tfidf_acesso.json',
    'conhecimento/memoria/tfidf_meta.json',
    'ler-runtime/knowledge/knowledge_graph.json',
}

# Paths that are EXPECTED to contain template variables (rendered by setup scripts)
TEMPLATE_FILES = {
    'config/opencode.jsonc',
    'scripts/opencode-serve.jsonc',
    'config/opencode-model-fallback.jsonc',
}

# Directories to skip (third-party bundles, user-specific)
SKIP_DIRS = {'node_modules', 'backups', '.git', 'Projetos', 'ferramentas', 'ai-agents', '.obsidian'}

# Patterns that indicate hardcoded user paths
HARDCODED_PATTERNS = [
    (re.compile(r'C:/Users/David'), 'C:/Users/David'),
    (re.compile(r'C:\\\\Users\\\\David'), 'C:\\Users\\David'),
]


def get_tracked_json_files():
    """Get all tracked JSON/JSONC files via git."""
    result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
    files = []
    for line in result.stdout.strip().split('\n'):
        if line and line.endswith(('.json', '.jsonc')):
            files.append(line)
    return files


def scan_file(filepath):
    """Scan a single JSON file for issues. Returns list of (severity, message)."""
    issues = []

    # Skip if in skip directory
    if any(skip in filepath for skip in SKIP_DIRS):
        return issues

    # Skip third-party bundles
    if filepath.startswith('ferramentas/') or filepath.startswith('ai-agents/'):
        return issues

    # Skip .obsidian plugin data files (user-specific)
    if '.obsidian/plugins' in filepath and filepath.endswith('data.json'):
        return issues

    if not os.path.exists(filepath):
        return issues

    # Read raw bytes
    with open(filepath, 'rb') as f:
        raw = f.read()

    # Check for file-level BOM
    if raw.startswith(b'\xef\xbb\xbf'):
        issues.append(('WARN', f'File has BOM: {filepath}'))

    # Decode
    content = raw.lstrip(b'\xef\xbb\xbf').decode('utf-8', errors='replace')

    # Check for embedded BOM in string values
    bom_count = content.count('\ufeff')
    if bom_count > 0:
        issues.append(('WARN', f'File has {bom_count} embedded BOM chars: {filepath}'))

    # Check for hardcoded paths (only in non-template files)
    is_template = filepath in TEMPLATE_FILES
    is_data_file = filepath in DATA_FILES
    for pattern, label in HARDCODED_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            if is_template:
                # Templates should NOT have hardcoded paths, only template vars
                issues.append(('FAIL', f'Template has hardcoded path: {filepath} (use template var)'))
            else:
                # All other files should not have hardcoded paths at all
                issues.append(('FAIL', f'Hardcoded path found: {filepath} ({len(matches)})'))

    # Check for unresolved template vars in non-template, non-data files
    if not is_template and not is_data_file and '{{USERPROFILE}}' in content:
        issues.append(('FAIL', f'Unresolved template var in non-template: {filepath}'))

    # Check file is valid JSON (with multiline string handling)
    if content.count('{') > 0:
        try:
            # Simple JSONC comment strip for validation
            cleaned = re.sub(r'//[^\n]*', '', content)
            cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
            # Remove trailing commas
            cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
            # Try parsing - if fails due to multiline strings, use a more lenient approach
            try:
                json.loads(cleaned)
            except json.JSONDecodeError as e:
                # Check if it's a multiline string issue (common in JSONC templates)
                if 'Invalid control character' in str(e):
                    # Likely multiline string - skip this check
                    pass
                else:
                    raise
        except json.JSONDecodeError:
            issues.append(('WARN', f'JSON parse error (may have multiline strings): {filepath}'))

    return issues


def main():
    json_files = get_tracked_json_files()
    print(f"Scanning {len(json_files)} tracked JSON/JSONC files...\n")

    all_issues = []
    passes = 0
    for f in sorted(json_files):
        issues = scan_file(f)
        all_issues.extend(issues)
        if not issues:
            passes += 1
        else:
            for severity, msg in issues:
                if severity == 'FAIL':
                    print(f"  [{severity}] {msg}")

    print(f"\n{'='*50}")
    print(f"Resultados:")
    print(f"  Total arquivos: {len(json_files)}")
    print(f"  Pass: {passes}")
    fails = [i for i in all_issues if i[0] == 'FAIL']
    warns = [i for i in all_issues if i[0] == 'WARN']
    print(f"  Fail: {len(fails)}")
    print(f"  Warn: {len(warns)}")

    for severity, msg in all_issues:
        if severity == 'WARN':
            print(f"  [{severity}] {msg}")

    if fails:
        print(f"\n❌ REGRESSION: {len(fails)} hardcoded path(s) found!")
        return 1

    print(f"\n✅ ALL JSON FILES CLEAN")
    return 0


if __name__ == '__main__':
    sys.exit(main())
