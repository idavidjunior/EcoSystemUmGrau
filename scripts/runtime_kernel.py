"""Kernel Permanente do Ecossistema.

Autoridade máxima. Nenhuma resposta é produzida sem passar pelo Kernel.
Controla regras, prioridades, contratos, políticas, formatos obrigatórios,
sequência de execução, validações e autorização para resposta.

O Kernel é agnóstico de LLM: a inteligência operacional vive aqui, não no modelo.

Uso CLI:
  python scripts/runtime_kernel.py status                 # estado do kernel
  python scripts/runtime_kernel.py check "<texto>"       # valida texto contra regras (contrato de saída)
  python scripts/runtime_kernel.py contrato-entrada "<objetivo>"
  python scripts/runtime_kernel.py pipeline              # fluxo obrigatório
  python scripts/runtime_kernel.py regras                # lista regras absolutas
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

CONSTITUICAO = os.path.join(BASE, 'config', 'agents', '00-system-rules.md')

# Sequência obrigatória de execução (nenhuma etapa pode ser pulada)
PIPELINE = [
    'Bootloader (restaura estado + verifica integridade)',
    'Kernel (autoriza e enquadra a tarefa)',
    'Memory Engine (carrega memória relevante)',
    'Context Loader (seleciona documentos/agentes relevantes)',
    'Conselho Permanente (somente se complexidade/criticidade alta)',
    'LER (somente se tarefa multi-passo ou exploração)',
    'Validador (verifica conformidade da resposta)',
    'Auditor (auditoria final contra Constituição/objetivo)',
    'Resposta Final (após autorização do Kernel)',
]

# Contrato de entrada obrigatório
ENTRADA_CONTRATO = {
    'objetivo': 'O que deve ser alcançado',
    'contexto': 'Estado atual do ecossistema',
    'restricoes': 'Limites e condições',
    'memoria_necessaria': 'Memórias que precisam ser carregadas',
    'ferramentas': 'Ferramentas e documentos disponíveis',
    'criterios_sucesso': 'Como saber que a tarefa foi concluída',
    'formato_esperado': 'Formato da resposta',
}

# Contrato de saída obrigatório
SAIDA_CONTRATO = {
    'resultado': 'O que foi entregue',
    'justificativa': 'Por que esta é a resposta correta',
    'verificacoes': 'Validações realizadas',
    'pendencias': 'O que ficou pendente',
    'proximos_passos': 'Recomendações de continuidade',
}


class Kernel:
    def __init__(self):
        self.rules = self._load_absolute_rules()
        self.status = 'ACTIVE'

    def _load_absolute_rules(self):
        """Extrai as regras absolutas da Constituição."""
        rules = []
        if not os.path.exists(CONSTITUICAO):
            return rules
        with open(CONSTITUICAO, encoding='utf-8') as f:
            content = f.read()
        # Regras absolutas numeradas dentro da cláusula pétrea de soberania
        section = content.split('# CLÁUSULA PÉTREA — SOBERANIA DO RUNTIME E DO KERNEL')
        if len(section) > 1:
            body = section[1].split('\n---')[0]
            for line in body.splitlines():
                line = line.strip()
                m = re.match(r'\d+\.\s+(.+)', line)
                if m:
                    rules.append(m.group(1))
        return rules

    def authorize(self, goal):
        """Enquadra a tarefa no contrato de entrada. Retorna contrato preenchido."""
        contract = {k: '' for k in ENTRADA_CONTRATO}
        contract['objetivo'] = goal.strip()
        contract['contexto'] = '(restaurar via runtime_boot)'
        return contract

    def validate_output(self, text, goal=''):
        """Valida uma resposta contra as regras do Kernel (contrato de saída).

        Retorna (ok, lista de falhas).
        """
        failures = []
        text = text or ''
        if not text.strip():
            failures.append('Resposta vazia')
        for rule in self.rules:
            rl = rule.lower()
            # Checagens heurísticas leves baseadas nas regras absolutas
            if 'memória' in rl and ('memória' not in text.lower() and
                                     'memory' not in text.lower() and goal):
                failures.append(f'Regra: "{rule}" — resposta não referencia memória/contexto')
            if 'validar' in rl and ('valid' not in text.lower() and
                                     'verific' not in text.lower()):
                failures.append(f'Regra: "{rule}" — resposta não declara validação realizada')
            if 'justificativa' in rl and ('justific' not in text.lower() and
                                           'porqu' not in text.lower()):
                failures.append(f'Regra: "{rule}" — resposta sem justificativa explícita')
        return (len(failures) == 0, failures)

    def authorize_response(self, text, goal=''):
        """Autorização final do Kernel para emitir a resposta."""
        ok, failures = self.validate_output(text, goal)
        if not ok:
            return False, failures
        return True, ['todas as regras absolutas respeitadas']

    def render_status(self):
        lines = ['=== KERNEL PERMANENTE ===', f'Status: {self.status}',
                 f'Regras absolutas: {len(self.rules)}']
        for r in self.rules:
            lines.append(f'  • {r}')
        lines.append('')
        lines.append('Pipeline obrigatório:')
        for i, step in enumerate(PIPELINE, 1):
            lines.append(f'  {i}. {step}')
        return '\n'.join(lines)

    def render_contract(self, kind='entrada'):
        contract = ENTRADA_CONTRATO if kind == 'entrada' else SAIDA_CONTRATO
        lines = [f'=== CONTRATO DE {kind.upper()} (obrigatório) ===']
        for k, v in contract.items():
            lines.append(f'  {k}: {v}')
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Kernel Permanente do Ecossistema')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('status')
    sub.add_parser('regras')
    sub.add_parser('pipeline')
    p_entrada = sub.add_parser('contrato-entrada')
    p_entrada.add_argument('objetivo', nargs='*', default=[])
    p_check = sub.add_parser('check')
    p_check.add_argument('texto', nargs='*', default=[])

    args = parser.parse_args()
    cmd = args.cmd or 'status'
    kernel = Kernel()

    if cmd == 'status':
        print(kernel.render_status())
    elif cmd == 'regras':
        for r in kernel.rules:
            print(f'  • {r}')
    elif cmd == 'pipeline':
        for i, step in enumerate(PIPELINE, 1):
            print(f'  {i}. {step}')
    elif cmd == 'contrato-entrada':
        print(kernel.render_contract('entrada'))
        if args.objetivo:
            goal = ' '.join(args.objetivo)
            contract = kernel.authorize(goal)
            print(f'\nContrato preenchido:\n  objetivo: {contract["objetivo"]}')
    elif cmd == 'check':
        text = ' '.join(args.texto)
        ok, failures = kernel.validate_output(text)
        if ok:
            print('[OK] Resposta conforme as regras do Kernel.')
        else:
            print('[REPROVADO]')
            for f in failures:
                print(f'  - {f}')
            sys.exit(1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
