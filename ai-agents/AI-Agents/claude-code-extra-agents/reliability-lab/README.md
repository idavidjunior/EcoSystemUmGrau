# Agent Reliability Lab

Este laboratorio mede qualidade de saida por agente com cenarios fixos.

## Como usar
1. Execute um agente para um cenario de `reliability-lab/scenarios/*.json`.
2. Salve a resposta em `reliability-lab/results/<scenario-id>.md`.
3. Rode:
```bash
python scripts/evaluate_reliability_lab.py
```

## Saidas
- `reliability-lab/reports/scorecard.json`
- `reliability-lab/reports/scorecard.md`
- `reliability-lab/reports/leaderboard.json`

## O que e medido
- Clareza
- Acionabilidade
- Risco de alucinacao (presenca de limitacoes/nao verificado)
- Consistencia
