# 2026-07-27 - Correcao dos 4 pontos finais do ecossistema

## Problemas resolvidos
1. **Paths fixos**: vigilante.ps1, ecosystem.ps1, SKILL.md agora usam env:USERPROFILE
2. **LER vs OpenCode**: documentado que LER tem engine MODULES (Python), OpenCode tem AGENTES (LLM). Sao complementares, nao duplicados.
3. **ecosystem learn**: varredura proativa que escaneia projetos Android + registra no knowledge graph
4. **Vigilante aprende sozinho**: timer diario executa ecosystem learn automaticamente
5. **Testes automatizados**: test-ecosystem.ps1 com 19 testes (exit code 0 = OK)
6. **opencode.jsonc regenerado**: do template com {{USERPROFILE}}
7. **SKILL.md**: paths corrigidos + secao de arquitetura LER vs OpenCode

## Decisoes
- LER engine modules sao diferentes de OpenCode agents (nao unificar codigo, apenas conceito)
- ecosystem learn roda automaticamente 1x/dia via vigilante
- test-ecosystem.ps1 cobre 14 categorias, 19 testes, saida clara PASS/FAIL/WARN
- Nao usar Write-Host em scripts que precisam capturar output (ecosystem.ps1 usa Write-Host para terminal, OK)

## Padrao
- Usar env:USERPROFILE em vez de paths fixos
- Timer + intervalo minimo para operacoes periodicas (learn 1x/dia, git sync 5min)
- Testes como script standalone, executavel a qualquer momento

## Conexoes

- [[cluster-hub-programacao]]