#!/usr/bin/env python3
"""Teste rápido dos skills MCP reais."""

import sys
sys.path.insert(0, '.')

from scripts.mcp_client_real import chamar_skill_conselheiro

for seam in ['cetico.analise-riscos', 'etica.conformidade', 'revisor.qualidade']:
    print(f'\n=== Testando {seam} ===')
    r = chamar_skill_conselheiro(seam, 'teste')
    sucesso = 'error' not in r
    print(f'Sucesso: {sucesso}')
    if 'text' in r:
        print(f'Resposta ({len(r["text"])} chars): {r["text"][:200]}...')
    if not sucesso:
        print(f'Erro: {r.get("error_message", "desconhecido")}')