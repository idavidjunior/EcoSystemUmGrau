#!/usr/bin/env python3
"""Check Links - Verificador de links quebrados (Markdown, HTML, imports)."""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
import aiohttp

async def check_url_async(session, url, timeout=10):
    """Verifica URL assincronamente."""
    try:
        async with session.head(url, timeout=aiohttp.ClientTimeout(total=timeout), allow_redirects=True) as resp:
            return url, resp.status, None
    except asyncio.TimeoutError:
        return url, 0, 'TIMEOUT'
    except aiohttp.ClientError as e:
        return url, 0, str(e)
    except Exception as e:
        return url, 0, str(e)

def check_url_sync(url, timeout=10):
    """Verifica URL sincronamente (fallback)."""
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'LinkChecker/1.0')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return url, resp.status, None
    except urllib.error.HTTPError as e:
        return url, e.code, None
    except urllib.error.URLError as e:
        return url, 0, str(e)
    except Exception as e:
        return url, 0, str(e)

def extract_markdown_links(content):
    """Extrai links de Markdown."""
    # [text](url) e ![alt](url)
    pattern = r'!?\[([^\]]*)\]\(([^)]+)\)'
    return [(m.group(2), m.group(1)) for m in re.finditer(pattern, content)]

def extract_html_links(content):
    """Extrai links de HTML."""
    links = []
    # href
    for m in re.finditer(r'href=["\']([^"\']+)["\']', content):
        links.append((m.group(1), 'href'))
    # src
    for m in re.finditer(r'src=["\']([^"\']+)["\']', content):
        links.append((m.group(1), 'src'))
    return links

# Python standard library modules to skip when checking local imports
PYTHON_STDLIB = frozenset({
    'os', 'sys', 'json', 're', 'time', 'datetime', 'pathlib', 'collections',
    'itertools', 'functools', 'typing', 'dataclasses', 'enum', 'abc',
    'hashlib', 'subprocess', 'threading', 'multiprocessing', 'asyncio',
    'urllib', 'http', 'socket', 'ssl', 'email', 'html', 'xml', 'csv',
    'sqlite3', 'pickle', 'copy', 'pprint', 'textwrap', 'string', 'math',
    'random', 'statistics', 'decimal', 'fractions', 'numbers', 'uuid',
    'base64', 'binascii', 'hmac', 'secrets', 'hashlib', 'inspect',
    'importlib', 'pkgutil', 'runpy', 'sysconfig', 'site', 'builtins',
    'warnings', 'logging', 'traceback', 'argparse', 'getopt', 'optparse',
    'shlex', 'cmd', 'readline', 'rlcompleter', 'doctest', 'unittest',
    'test', 'venv', 'ensurepip', 'zipapp', 'tarfile', 'gzip', 'bz2',
    'lzma', 'zipfile', 'csv', 'configparser', 'tomllib', 'json', 'plistlib',
    'sqlite3', 'dbm', 'shelve', 'marshal', 'struct', 'array', 'memoryview',
    'io', 'os', 'sys', 'time', 'datetime', 'calendar', 'zoneinfo', 'locale',
    'gettext', 'textwrap', 'string', 're', 'difflib', 'fnmatch', 'glob',
    'linecache', 'shutil', 'filecmp', 'tempfile', 'stat', 'fileinput',
    'pathlib', 'os.path', 'glob', 'fnmatch', 'errno', 'ctypes', 'mmap',
    'signal', 'resource', 'select', 'asyncore', 'asynchat', 'socket',
    'ssl', 'selectors', 'asyncio', 'threading', 'multiprocessing',
    'concurrent', 'subprocess', 'sched', 'queue', 'contextvars', 'weakref',
    'types', 'copy', 'pprint', 'reprlib', 'enum', 'dataclasses', 'abc',
    'collections', 'heapq', 'bisect', 'array', 'weakref', 'types',
    'collections.abc', 'typing', 'numbers', 'math', 'cmath', 'decimal',
    'fractions', 'random', 'statistics', 'itertools', 'functools',
    'operator', 'inspect', 'dis', 'ast', 'symtable', 'symbol', 'token',
    'keyword', 'tokenize', 'tabnanny', 'pyclbr', 'py_compile', 'compileall',
    'importlib', 'pkgutil', 'modulefinder', 'runpy', 'importlib.metadata',
    'importlib.resources', 'zipimport', 'pkgutil', 'importlib.abc',
    'importlib.machinery', 'importlib.util', 'sysconfig', 'site',
    'platform', 'os', 'sys', 'time', 'datetime', 'calendar', 'zoneinfo',
    'locale', 'gettext', 'codecs', 'encodings', 'unicodedata', 'stringprep',
    'readline', 'rlcompleter', 'cmd', 'shlex', 'optparse', 'argparse',
    'getopt', 'fileinput', 'stat', 'filecmp', 'tempfile', 'glob', 'fnmatch',
    'linecache', 'shutil', 'macpath', 'dircache', 'statvfs', 'fcntl',
    'termios', 'tty', 'pty', 'signal', 'popen2', 'pipes', 'posix',
    'pwd', 'grp', 'crypt', 'spwd', 'resource', 'nis', 'syslog', 'commands',
    'asyncio', 'selectors', 'select', 'socket', 'ssl', 'signal', 'mmap',
    'ctypes', 'errno', 'resource', 'syslog', 'sys', 'os', 'time',
    'datetime', 'calendar', 'zoneinfo', 'locale', 'gettext', 'codecs',
    'encodings', 'unicodedata', 'stringprep', 'readline', 'rlcompleter',
    'cmd', 'shlex', 'optparse', 'argparse', 'getopt', 'fileinput', 'stat',
    'filecmp', 'tempfile', 'glob', 'fnmatch', 'linecache', 'shutil',
    'macpath', 'dircache', 'statvfs', 'fcntl', 'termios', 'tty', 'pty',
    'signal', 'popen2', 'pipes', 'posix', 'pwd', 'grp', 'crypt', 'spwd',
    'resource', 'nis', 'syslog', 'commands', 'asyncio', 'selectors',
    'select', 'socket', 'ssl', 'signal', 'mmap', 'ctypes', 'errno',
    'resource', 'syslog', 'sys', 'os', 'time', 'datetime', 'calendar',
    'zoneinfo', 'locale', 'gettext', 'codecs', 'encodings', 'unicodedata',
    'stringprep', 'readline', 'rlcompleter', 'cmd', 'shlex', 'optparse',
    'argparse', 'getopt', 'fileinput', 'stat', 'filecmp', 'tempfile',
    'glob', 'fnmatch', 'linecache', 'shutil', 'macpath', 'dircache',
    'statvfs', 'fcntl', 'termios', 'tty', 'pty', 'signal', 'popen2',
    'pipes', 'posix', 'pwd', 'grp', 'crypt', 'spwd', 'resource', 'nis',
    'syslog', 'commands',
})

def extract_imports_python(content):
    """Extrai imports Python."""
    imports = []
    for m in re.finditer(r'^(?:from\s+(\S+)\s+import|import\s+(\S+))', content, re.MULTILINE):
        mod = m.group(1) or m.group(2)
        if mod and not mod.startswith('.'):
            # Skip standard library modules
            root_mod = mod.split('.')[0]
            if root_mod in PYTHON_STDLIB:
                continue
            imports.append((mod, 'import'))
    return imports

def extract_imports_js_ts(content):
    """Extrai imports JS/TS."""
    imports = []
    # import ... from '...'
    for m in re.finditer(r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', content):
        imports.append((m.group(1), 'import'))
    # require('...')
    for m in re.finditer(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content):
        imports.append((m.group(1), 'require'))
    return imports

async def check_file_links(file_path, base_url, session, results):
    """Verifica links em um arquivo."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except:
        return
    
    links = []
    
    if file_path.suffix in ('.md', '.markdown'):
        links = extract_markdown_links(content)
    elif file_path.suffix in ('.html', '.htm'):
        links = extract_html_links(content)
    elif file_path.suffix == '.py':
        links = extract_imports_python(content)
    elif file_path.suffix in ('.js', '.ts', '.jsx', '.tsx'):
        links = extract_imports_js_ts(content)
    
    for link, context in links:
        # Skip anchors
        if link.startswith('#'):
            continue
        # Skip mailto, tel, etc
        if ':' in link and not link.startswith(('http://', 'https://', '//')):
            continue
        
        # Resolve relative URLs
        if link.startswith('//'):
            check_url = 'https:' + link
        elif link.startswith('/'):
            if base_url:
                check_url = urljoin(base_url, link)
            else:
                continue  # Can't check local paths without base
        elif not link.startswith(('http://', 'https://')):
            # Relative path - check if file exists locally
            local_path = (file_path.parent / link).resolve()
            if local_path.exists():
                results.append({'file': str(file_path), 'link': link, 'type': 'local', 'status': 'OK', 'context': context})
            else:
                results.append({'file': str(file_path), 'link': link, 'type': 'local', 'status': 'BROKEN', 'error': 'File not found', 'context': context})
            continue
        else:
            check_url = link
        
        # Check external URL
        if session:
            url, status, error = await check_url_async(session, check_url)
        else:
            url, status, error = check_url_sync(check_url)
        
        if error or status >= 400:
            results.append({'file': str(file_path), 'link': url, 'type': 'external', 'status': 'BROKEN', 'code': status, 'error': error, 'context': context})
        else:
            results.append({'file': str(file_path), 'link': url, 'type': 'external', 'status': 'OK', 'code': status, 'context': context})

async def main_async(args):
    path = Path(args.path).resolve()
    results = []
    
    # Collect files
    extensions = {'.md', '.markdown', '.html', '.htm', '.py', '.js', '.ts', '.jsx', '.tsx'}
    exclude_dirs = {'node_modules', '.git', '__pycache__', 'venv', 'env', 'dist', 'build', '.venv'}
    
    files = []
    for ext in extensions:
        for f in path.rglob(f'*{ext}'):
            if not any(d in f.parts for d in exclude_dirs):
                files.append(f)
    
    print(f'Verificando {len(files)} arquivos...')
    
    # Async HTTP session
    connector = aiohttp.TCPConnector(limit=20)
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [check_file_links(f, args.base_url, session, results) for f in files]
        await asyncio.gather(*tasks)
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Verifica links quebrados')
    parser.add_argument('path', nargs='?', default='.', help='Diretório do projeto')
    parser.add_argument('--base-url', help='Base URL para links relativos (ex: https://example.com)')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--external-only', action='store_true', help='Apenas links externos')
    parser.add_argument('--local-only', action='store_true', help='Apenas links locais')
    args = parser.parse_args()
    
    try:
        results = asyncio.run(main_async(args))
    except ImportError:
        # Fallback sync
        print('aiohttp não disponível, usando modo síncrono...')
        import urllib.request
        import urllib.error
        # Simplified sync version would go here
        results = []
    
    # Filter
    if args.external_only:
        results = [r for r in results if r['type'] == 'external']
    if args.local_only:
        results = [r for r in results if r['type'] == 'local']
    
    broken = [r for r in results if r['status'] == 'BROKEN']
    ok = [r for r in results if r['status'] == 'OK']
    
    if args.format == 'json':
        print(json.dumps({'broken': broken, 'ok': ok, 'total': len(results)}, indent=2, ensure_ascii=False))
        return
    
    print(f'\n=== LINK CHECK RESULTS ===')
    print(f'Total: {len(results)} | OK: {len(ok)} | BROKEN: {len(broken)}\n')
    
    if broken:
        print('--- LINKS QUEBRADOS ---')
        for r in broken:
            loc = f"{r['file']}:{r.get('context', '')}"
            if r['type'] == 'external':
                print(f"  [EXTERNAL] {r['link']} -> {r.get('code', 'ERR')}: {r.get('error', '')}")
            else:
                print(f"  [LOCAL] {r['link']} -> NOT FOUND")
            print(f"    em: {loc}")
            print()
    else:
        print('Todos os links OK!')

if __name__ == '__main__':
    main()