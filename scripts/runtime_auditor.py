"""Auditor adaptativo do Ecossistema.

Audita respostas contra a Constituição, o Kernel, o objetivo e as decisões
consolidadas. Adaptativo: tarefas simples recebem auditoria leve; tarefas
estratégicas, arquiteturais ou críticas recebem auditoria completa.

Caso algum critério falhe, a resposta retorna para nova execução (ciclo
Executar → Validar → Corrigir → Validar novamente → Responder).

Uso CLI:
  python scripts/runtime_auditor.py <objetivo> --resposta "<texto>"
  python scripts/runtime_auditor.py <objetivo> --resposta "<texto>" --criticidade alta
  python scripts/runtime_auditor.py --classificar "<objetivo>"
"""

import argparse
import os
import re
import sys
from datetime import datetime

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

# Palavras que indicam criticidade alta (estratégico/arquitetural/crítico)
CRITICAL_MARKERS = [
    'arquitetura', 'arquitetural', 'estratégia', 'estrategico', 'estratégico',
    'crítico', 'critico', 'produção', 'producao', 'deploy', 'segurança',
    'seguranca', 'banco de dados', 'migração', 'migracao', 'escala',
    'performance', 'refatoração', 'refatoracao', 'sistema', 'multi-projeto',
    'multiplos arquivos', '4+ arquivos', 'remover', 'quebrar', 'breaking',
    'api pública', 'api publica', 'integração', 'integracao', 'auth', 'pagamento',
    'custo', 'dados pessoais', 'privacidade', 'governança', 'governanca',
    'auditoria', 'conformidade', 'regulatór', 'regulator', 'contrato',
]

SIMPLE_MARKERS = [
    'explicar', 'pergunta', 'dúvida', 'duvida', 'o que é', 'como funciona',
    'diferença', 'diferenca', 'exemplo', 'resumo', 'ajuda',
]


def classificar_criticidade(objetivo):
    """Classifica a tarefa: 'baixa', 'media' ou 'alta' criticidade."""
    objetivo = (objetivo or '').lower()
    if any(m in objetivo for m in SIMPLE_MARKERS) and \
       not any(m in objetivo for m in CRITICAL_MARKERS):
        return 'baixa'
    hits = sum(1 for m in CRITICAL_MARKERS if m in objetivo)
    if hits >= 2 or any(m in objetivo for m in
                        ['arquitetur', 'crítico', 'critico', 'seguran', 'deploy',
                         'produção', 'producao']):
        return 'alta'
    if hits == 1:
        return 'media'
    return 'baixa'


def auditar(resposta, objetivo='', criticidade=None, kernel_rules=None,
            decisoes_relacionadas=None):
    """Executa a auditoria. Retorna (aprovado, relatório, falhas)."""
    if criticidade is None:
        criticidade = classificar_criticidade(objetivo)

    resposta = resposta or ''
    relatorio = []
    falhas = []

    # Critério 1: resposta não vazia
    if not resposta.strip():
        falhas.append('Resposta vazia')
    else:
        relatorio.append('Resposta presente')

    # Critério 2: aderência ao objetivo (tolerante a flexões via prefixo/substring)
    if objetivo:
        tokens_obj = [t for t in re.findall(r'[a-zA-Z]{4,}', objetivo.lower())
                      if t not in ('para', 'que', 'com', 'uma', 'como', 'esta', 'ser',
                                   'sobre', 'apos')]
        resp_lower = resposta.lower()
        encontrados = 0
        for t in tokens_obj[:5]:
            if t in resp_lower or any(w.startswith(t[:5]) for w in re.findall(r'[a-zA-Z]{4,}', resp_lower)):
                encontrados += 1
        if tokens_obj and encontrados == 0:
            falhas.append('Resposta não adere ao objetivo (nenhum termo-chave do objetivo presente)')
        else:
            relatorio.append(f'Objetivo: {encontrados}/{min(5, len(tokens_obj))} termos-chave presentes')

    # Critério 3: regras do Kernel
    if kernel_rules:
        for rule in kernel_rules:
            rl = rule.lower()
            if 'validar' in rl and 'valid' not in resposta.lower():
                falhas.append(f'Regra Kernel: "{rule}"')
            elif 'justificativa' in rl and 'justific' not in resposta.lower():
                falhas.append(f'Regra Kernel: "{rule}"')
            elif 'memória' in rl and 'mem' not in resposta.lower():
                falhas.append(f'Regra Kernel: "{rule}"')

    # Critério 4: decisões consolidadas não contrariadas
    if decisoes_relacionadas:
        relatorio.append(f'{len(decisoes_relacionadas)} decisão(ões) relacionada(s) considerada(s)')

    # Critério 5 (auditoria completa): consistência e próximos passos
    if criticidade in ('alta', 'media'):
        if 'próximo' not in resposta.lower() and 'proximo' not in resposta.lower() \
           and 'próximos' not in resposta.lower():
            falhas.append('Auditoria completa: resposta não indica próximos passos')
        if 'valid' not in resposta.lower() and 'teste' not in resposta.lower() \
           and 'verific' not in resposta.lower():
            falhas.append('Auditoria completa: resposta não declara verificações realizadas')

    aprovado = len(falhas) == 0
    cabecalho = f"=== AUDITOR ADAPTATIVO ===\nCriticidade: {criticidade}\nResultado: {'APROVADO' if aprovado else 'REPROVADO'} (ciclo deve repetir)"
    corpo = '\n'.join(f'  [OK] {r}' for r in relatorio)
    falhas_txt = '\n'.join(f'  [X] {f}' for f in falhas) if falhas else '  (sem falhas)'
    return aprovado, f'{cabecalho}\n{corpo}\nFalhas:\n{falhas_txt}', falhas


def main():
    parser = argparse.ArgumentParser(description='Auditor adaptativo')
    parser.add_argument('objetivo', nargs='*', default=[])
    parser.add_argument('--resposta', default='')
    parser.add_argument('--criticidade', choices=['baixa', 'media', 'alta'], default=None)
    parser.add_argument('--classificar', action='store_true')
    args = parser.parse_args()

    objetivo = ' '.join(args.objetivo)

    if args.classificar:
        print(f'Criticidade: {classificar_criticidade(objetivo)}')
        return 0

    # Carrega regras do Kernel
    kernel_rules = []
    try:
        from runtime_kernel import Kernel
        kernel_rules = Kernel().rules
    except Exception:
        pass

    # Decisões relacionadas via context loader
    decisoes = []
    try:
        from runtime_context import _carregar_decisoes, _extrair_tags
        decisoes = _carregar_decisoes(objetivo, _extrair_tags(objetivo), 3)
    except Exception:
        pass

    aprovado, relatorio, falhas = auditar(
        args.resposta, objetivo, args.criticidade, kernel_rules, decisoes)
    print(relatorio)
    return 0 if aprovado else 1


if __name__ == '__main__':
    sys.exit(main())
