# Etica

**Hub de conhecimento ético do ecossistema.** Cláusula Pétrea de Deveres Externos.

## Estrutura de Governança Ética

- **Constituição** — Cláusula Pétrea de Deveres Externos
  `config/agents/00-system-rules.md`
- **Agente de Ética** — `config/agents/04-etica.md` (gate operacional obrigatório)
- **Preflight Ético** — `scripts/preflight_etica.py` (bloqueia entrega se falhar)
- **Política de Retenção** — `conhecimento/etica/POLITICA_RETENCAO.md`
- **Inventário de Dados** — `conhecimento/etica/inventario_dados.json`
- **Rotação de Dados** — `scripts/rotacao_dados.py`

## Comandos

```bash
# Gate ético antes de toda entrega
python scripts/preflight_etica.py

# Mapear dados sensíveis
python scripts/preflight_etica.py --data-inventory

# Aplicar política de retenção
python scripts/rotacao_dados.py
```

## Decisões éticas registradas
- [[cláusula-pétrea-de-deveres-externos-do-ecossistema]]
