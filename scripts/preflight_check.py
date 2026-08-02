"""Pre-flight check: valida config, MCP e plugins ANTES de deployar.
Clausula Petrea: se falhar, NAO aplica a alteracao."""
import json, os, sys, subprocess, traceback
import re
from pathlib import Path

USERPROFILE = str(Path.home())
BASE = str(Path(__file__).resolve().parent.parent)
DEPLOYED = os.path.join(USERPROFILE, '.config', 'opencode', 'opencode.jsonc')
BACKUP = DEPLOYED + '.bak'

ERRORS = []
WARNS = []

def check(label, condition, detail=''):
    if condition:
        print(f'  [PASS] {label}')
        return True
    else:
        msg = f'{label}: {detail}' if detail else label
        ERRORS.append(msg)
        print(f'  [FAIL] {msg}')
        return False

def check_json(path, label='JSON'):
    try:
        with open(path, encoding='utf-8-sig') as f:
            data = json.load(f)
        return check(f'{label} JSON valido', True), data
    except Exception as e:
        check(f'{label} JSON valido', False, str(e))
        return False, None

def expand_path(path_str):
    """Expand {env:USERPROFILE} and legacy {{USERPROFILE}} template vars."""
    result = path_str.replace('{env:USERPROFILE}', USERPROFILE.replace('\\', '/'))
    result = result.replace('{{USERPROFILE}}', USERPROFILE.replace('\\', '/'))
    return result

def test_mcp_server(server_name, command, args):
    """Test an MCP server: initialize + tools/list must complete in 5s."""
    print(f'  Testing MCP: {server_name}...')
    try:
        # Expand template vars if present
        cmd_expanded = expand_path(command)
        args_expanded = [expand_path(a) for a in args]
        proc = subprocess.Popen(
            [cmd_expanded] + args_expanded,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=BASE)
        init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
        tools = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
        stdout, stderr = proc.communicate(input=init + tools, timeout=5)
        proc.kill()
        if stderr and 'Error' in stderr:
            return check(f'MCP {server_name}', False, stderr[:200])
        lines = [l for l in stdout.strip().split('\n') if l.strip()]
        if len(lines) >= 2:
            result = json.loads(lines[1])  # tools/list response
            if 'result' in result and 'tools' in result['result']:
                n_tools = len(result['result']['tools'])
                return check(f'MCP {server_name}', True, f'{n_tools} tools')
        return check(f'MCP {server_name}', False, 'No valid tools/list response')
    except subprocess.TimeoutExpired:
        proc.kill()
        return check(f'MCP {server_name}', False, 'Timeout (5s)')
    except Exception as e:
        return check(f'MCP {server_name}', False, str(e)[:200])

def check_mcp_servers(cfg, label='Config', test_servers=True):
    """Validate MCP server configs in a given config dict.

    Suporta o formato novo (opencode 1.x): mcp.<nome> com "command" sendo lista
    [cmd, arg1, ...], e o formato legado: mcp.servers.<nome> com command + args.
    """
    mcp = cfg.get('mcp')
    if not mcp:
        WARNS.append(f'{label}: sem servidor MCP configurado (opcional)')
        print(f'  [WARN] {label}: sem servidor MCP configurado (opcional)')
        return
    servers = mcp.get('servers', mcp) if isinstance(mcp, dict) else {}
    if not servers:
        WARNS.append(f'{label}: sem servidor MCP configurado (opcional)')
        print(f'  [WARN] {label}: sem servidor MCP configurado (opcional)')
        return
    check(f'{label}: {len(servers)} MCP servidor(es)', True)
    for sname, sconfig in servers.items():
        if not isinstance(sconfig, dict):
            continue
        cmd = sconfig.get('command', '')
        args = sconfig.get('args', [])
        if isinstance(cmd, list):
            args = cmd[1:] + (list(args) if isinstance(args, list) else [])
            cmd = cmd[0] if cmd else ''
        if not cmd:
            check(f'{label}: MCP {sname} sem command', False)
            continue
        if 'npx' in str(cmd).lower():
            check(f'{label}: MCP {sname} npx proibido', False,
                  'Servidores npx travam inicializacao do OpenCode. Use Python puro.')
            continue
        if test_servers:
            test_mcp_server(sname, cmd, args)

def run():
    print('========================================')
    print('  PRE-FLIGHT CHECK - Clausula Petrea')
    print('========================================\n')

    # 1. Template config (estrutura, sem testar servers pq tem {{USERPROFILE}})
    print('[1] Template config (estrutura)')
    template_path = os.path.join(BASE, 'config', 'opencode.jsonc')
    ok, cfg = check_json(template_path, 'Template')
    if ok and cfg:
        required_keys = ['plugin', 'provider', 'instructions']
        for key in required_keys:
            check(f'Config tem: {key}', key in cfg)
        check_mcp_servers(cfg, 'Template', test_servers=False)

    # 2. Deployed config (estrutura + testar servers)
    print('\n[2] Deployed config (estrutura + MCP real)')
    if os.path.exists(DEPLOYED):
        ok2, cfg2 = check_json(DEPLOYED, 'Deployed')
        if ok2 and cfg2:
            check('Deployed tem: instructions', 'instructions' in cfg2)
            for opt in ['plugin', 'provider', 'mcp']:
                if cfg2.get(opt) is None:
                    WARNS.append(f'Deployed sem {opt} (opcional)')
                    print(f'  [WARN] Deployed sem {opt} (opcional)')
            with open(DEPLOYED, encoding='utf-8-sig') as f:
                content = f.read()
            check('Deployed sem npx', 'npx' not in content, 'npx encontrado!')
            check_mcp_servers(cfg2, 'Deployed', test_servers=True)
    else:
        check('Deployed config existe', False, f'{DEPLOYED} nao encontrado')

    # 3. Rollback capability
    print('\n[3] Rollback capability')
    if os.path.exists(BACKUP):
        check('Backup disponivel', True)
    else:
        WARNS.append('Sem backup (opencode.jsonc.bak). Crie backup antes de alterar.')
        print('  [WARN] Sem backup. Crie backup antes de alterar.')

    # 4. Agents integrity
    print('\n[4] Agents')
    agents_dir = os.path.join(BASE, 'config', 'agents')
    if os.path.isdir(agents_dir):
        agent_files = [f for f in os.listdir(agents_dir) if f.endswith('.md')]
        check(f'{len(agent_files)} agent files', len(agent_files) >= 15)
    else:
        check('Agents dir', False)

    # 5. Regras 3 camadas (AGENTS.md + opencode.jsonc instructions + constituicao deployed)
    print('\n[5] Regras do ecossistema (3 camadas)')
    try:
        import subprocess as sp
        r = sp.run([sys.executable, os.path.join(BASE, 'scripts', 'sync_rules.py'), 'check'],
                   capture_output=True, text=True, timeout=30)
        out = (r.stdout + r.stderr).strip()
        for line in out.splitlines():
            if line.startswith('[DIVERGENCIA]'):
                check(f'Regras consistentes', False, line.replace('[DIVERGENCIA] ', ''))
        if not any(l.startswith('[DIVERGENCIA]') for l in out.splitlines()):
            check('Regras 3 camadas consistentes', True)
    except Exception as e:
        check('Regras 3 camadas', False, str(e)[:200])

    # Summary
    print('\n========================================')
    if not ERRORS:
        print('  RESULTADO: TODOS TESTES PASSARAM')
        print('  Pode aplicar a alteracao com seguranca.')
    else:
        print(f'  RESULTADO: {len(ERRORS)} ERRO(S)')
        for e in ERRORS:
            print(f'    [ERR] {e}')
        print('  ALTERACAO BLOQUEADA. Corrija os erros antes de aplicar.')
    print('========================================')
    return len(ERRORS) == 0

if __name__ == '__main__':
    success = run()
    sys.exit(0 if success else 1)
