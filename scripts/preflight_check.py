"""Pre-flight check: valida config, MCP e plugins ANTES de deployar.
Clausula Petrea: se falhar, NAO aplica a alteracao."""
import json, os, sys, subprocess, traceback
import re

USERPROFILE = os.environ.get('USERPROFILE', 'C:\\Users\\Playtec-bancada')
BASE = os.path.join(USERPROFILE, 'Desktop', 'Codigos', 'EcoSystemUmGrau')
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
    """Expand {{USERPROFILE}} template vars."""
    return path_str.replace('{{USERPROFILE}}', USERPROFILE.replace('\\', '/'))

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
    """Validate MCP server configs in a given config dict."""
    mcp = cfg.get('mcp', {})
    servers = mcp.get('servers', {}) if mcp else {}
    if not servers:
        check(f'{label}: MCP servers', False, 'Nenhum servidor MCP configurado')
        return
    check(f'{label}: {len(servers)} MCP servidor(es)', True)
    for sname, sconfig in servers.items():
        cmd = sconfig.get('command', '')
        args = sconfig.get('args', [])
        if not cmd:
            check(f'{label}: MCP {sname} sem command', False)
            continue
        if 'npx' in cmd.lower():
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
            for key in ['plugin', 'provider', 'mcp', 'instructions']:
                has = cfg2.get(key) is not None
                check(f'Deployed tem: {key}', has)
            with open(DEPLOYED, encoding='utf-8-sig') as f:
                content = f.read()
            check('Deployed sem npx', 'npx' not in content, 'npx encontrado!')
            check_mcp_servers(cfg2, 'Deployed', test_servers=True)
    else:
        check('Deployed config existe', False, f'{DEPLOYED} nao encontrado')

    # 3. Rollback capability
    print('\n[3] Rollback capability')
    check('Backup disponivel', os.path.exists(BACKUP), 'Crie backup antes de alterar.')

    # 4. Agents integrity
    print('\n[4] Agents')
    agents_dir = os.path.join(BASE, 'config', 'agents')
    if os.path.isdir(agents_dir):
        agent_files = [f for f in os.listdir(agents_dir) if f.endswith('.md')]
        check(f'{len(agent_files)} agent files', len(agent_files) >= 15)
    else:
        check('Agents dir', False)

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
