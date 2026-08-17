#!/usr/bin/env python3
"""
install_git_hook.py — Instala/Remove Git Hook para Gate de Persistência

O hook pre-commit verifica se o commit está sendo feito via persistencia.ps1.
Se não estiver, BLOQUEIA o commit e orienta usar o gate.

Uso:
  python scripts/install_git_hook.py install   # instala hook pre-commit
  python scripts/install_git_hook.py remove    # remove hook pre-commit
  python scripts/install_git_hook.py status    # verifica se hook está instalado
"""
import sys
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GIT_HOOKS_DIR = BASE / '.git' / 'hooks'
PRE_COMMIT_HOOK = GIT_HOOKS_DIR / 'pre-commit'

HOOK_CONTENT = '''#!/usr/bin/env python3
"""
Git pre-commit hook — Gate de Persistência EcoSystemUmGrau

Verifica se o commit está sendo feito via persistencia.ps1 (gate único).
Se NÃO estiver, BLOQUEIA o commit e orienta usar o gate.

EXCEÇÕES (permitem commit direto):
- Commits de merge
- Commits com mensagem contendo "[gate]" ou "persistencia.ps1" ou "run-sync"
- Commits em arquivos apenas de configuração local (ex: .env.local)
"""
import sys
import subprocess
import re
from pathlib import Path

def get_commit_msg():
    """Obtém a mensagem do commit que está sendo criado."""
    # Tenta ler de .git/COMMIT_EDITMSG
    commit_editmsg = Path('.git') / 'COMMIT_EDITMSG'
    if commit_editmsg.exists():
        return commit_editmsg.read_text(encoding='utf-8', errors='replace').strip()
    return ''

def is_merge_commit():
    """Verifica se é um commit de merge."""
    merge_head = Path('.git') / 'MERGE_HEAD'
    return merge_head.exists()

def is_via_gate(msg: str) -> bool:
    """Verifica se o commit menciona uso do gate."""
    msg_lower = msg.lower()
    gate_indicators = [
        '[gate]',
        'persistencia.ps1',
        'run-sync',
        'gate persist',
    ]
    return any(ind in msg_lower for ind in gate_indicators)

def main():
    # Se é merge commit, permite
    if is_merge_commit():
        print('[GATE] Merge commit detectado — permitido.')
        return 0
    
    msg = get_commit_msg()
    
    # Se mensagem indica uso do gate, permite
    if is_via_gate(msg):
        print(f'[GATE] Commit via gate detectado — permitido.')
        return 0
    
    # BLOQUEIA: commit direto sem gate
    print('='*70)
    print('[BLOQUEADO] Commit direto detectado — Gate de Persistência ativo!')
    print('='*70)
    print()
    print('O EcoSystemUmGrau exige que TODOS os commits passem pelo gate único:')
    print('  scripts/persistencia.ps1')
    print()
    print('Para commitar corretamente, use um destes comandos:')
    print()
    print('  # Commit automático via gate (recomendado):')
    print('  powershell -ExecutionPolicy Bypass -File scripts/persistencia.ps1 run-sync')
    print()
    print('  # Commit manual via gate:')
    print('  powershell -ExecutionPolicy Bypass -File scripts/persistencia.ps1 commit -Mensagem "sua mensagem" -Push')
    print()
    print('  # Se for commit de merge ou hotfix emergencial, adicione "[gate]" na mensagem:')
    print('  git commit -m "hotfix: correção urgente [gate]"')
    print()
    print('Para desativar temporariamente (NÃO RECOMENDADO):')
    print('  git commit --no-verify -m "mensagem"')
    print()
    print('='*70)
    return 1

if __name__ == '__main__':
    sys.exit(main())
'''

def instalar():
    """Instala o hook pre-commit."""
    GIT_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Cria arquivo Python do hook
    hook_py = GIT_HOOKS_DIR / 'pre-commit.py'
    
    # Backup se já existir
    if PRE_COMMIT_HOOK.exists():
        backup = PRE_COMMIT_HOOK.with_suffix('.backup')
        PRE_COMMIT_HOOK.rename(backup)
        print(f'[INFO] Hook anterior salvo como: {backup}')
    if hook_py.exists():
        backup = hook_py.with_suffix('.backup')
        hook_py.rename(backup)
    
    hook_py.write_text(HOOK_CONTENT, encoding='utf-8')
    
    # SOLUÇÃO WINDOWS: Cria pre-commit.cmd (extensão .cmd que git no Windows reconhece como executável)
    hook_cmd = GIT_HOOKS_DIR / 'pre-commit.cmd'
    wrapper_content = f'''@echo off
REM Git pre-commit hook wrapper - Gate de Persistência EcoSystemUmGrau
"{sys.executable}" "{hook_py}" %*
if errorlevel 1 exit /b 1
'''
    hook_cmd.write_text(wrapper_content, encoding='utf-8')
    
    # Cria também pre-commit (sem extensão) como cópia do .cmd para compatibilidade
    PRE_COMMIT_HOOK.write_text(wrapper_content, encoding='utf-8')
    
    # Tenta tornar executável (Git Bash)
    try:
        os.chmod(PRE_COMMIT_HOOK, 0o755)
        os.chmod(hook_cmd, 0o755)
        os.chmod(hook_py, 0o755)
    except:
        pass
    
    print(f'[OK] Hook pre-commit instalado:')
    print(f'  Script Python: {hook_py}')
    print(f'  Hook CMD: {hook_cmd}')
    print(f'  Entry point: {PRE_COMMIT_HOOK}')
    print('[INFO] Commits diretos agora serão BLOQUEADOS. Use persistencia.ps1 para commitar.')
    return 0

def remover():
    """Remove o hook pre-commit."""
    if PRE_COMMIT_HOOK.exists():
        PRE_COMMIT_HOOK.unlink()
        print(f'[OK] Hook pre-commit removido.')
    else:
        print('[INFO] Hook pre-commit não estava instalado.')
    
    # Restaura backup se existir
    backup = PRE_COMMIT_HOOK.with_suffix('.backup')
    if backup.exists():
        backup.rename(PRE_COMMIT_HOOK)
        print(f'[OK] Hook anterior restaurado do backup.')
    return 0

def status():
    """Verifica se hook está instalado."""
    if PRE_COMMIT_HOOK.exists():
        print('[OK] Hook pre-commit INSTALADO')
        print(f'  Arquivo: {PRE_COMMIT_HOOK}')
        # Verifica conteúdo
        content = PRE_COMMIT_HOOK.read_text(encoding='utf-8')
        if 'Gate de Persistência' in content:
            print('  Tipo: Gate de Persistência EcoSystemUmGrau')
        else:
            print('  Tipo: Outro (conteúdo diferente)')
    else:
        print('[INFO] Hook pre-commit NÃO instalado.')
    return 0

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    cmd = sys.argv[1]
    if cmd == 'install':
        return instalar()
    elif cmd == 'remove':
        return remover()
    elif cmd == 'status':
        return status()
    else:
        print(f'[ERRO] Comando desconhecido: {cmd}')
        print(__doc__)
        return 1

if __name__ == '__main__':
    sys.exit(main())