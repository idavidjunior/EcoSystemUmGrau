# Quickstart

## 1) Verificar ambiente
Execute:
```text
/doctor
```

## 2) Usar por objetivo
- Investigar incidente: `/forensic`
- Revisar codigo IA: `/verify`
- Simular incidente: `/simulate`
- Auditar seguranca/dependencias: `/audit`
- Analisar performance: `/perf`
- Navegar e extrair web: `/navigate`

## 3) Fluxo recomendado
1. `doctor` para pre-condicoes.
2. Comando especialista para o objetivo.
3. Validar riscos e proximos passos no relatorio final.

## Exemplos de prompt
- "Rode `/forensic` e encontre causa raiz do erro 500."
- "Use `/verify` neste PR e priorize achados criticos."
- "Execute `/audit` e gere plano de mitigacao por severidade."

## Instalacao para usuarios
- Via plugin: veja [README](../README.md#instalacao-em-1-minuto)
- Via script: `install.ps1` (Windows) ou `install.sh` (Linux/macOS)
