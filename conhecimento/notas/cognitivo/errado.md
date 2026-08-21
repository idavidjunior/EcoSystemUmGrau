---
tags: [ativo, cognitivo, conexao, device, find, general]
aliases: [ERRADO]
date: 2026-08-21
---

# ERRADO

**Dominio:** general

---
tipo: erro
tags: [adb, tailscale, scrcpy, android, conexao]
data: 2026-08-18
contexto: scrcpy nao encontrava dispositivo ADB via Tailscale
decisao: Corrigir caminho do ADB em adb_auto_connect.py para tentar multiplos caminhos
impacto: Tailscale agora funciona como alternativa viavel para conexao ADB
---

## Problema

O scrcpy retornava "Could not find any ADB device" mesmo com Tailscale ativo.

## Causa

O `adb_auto_connect.py` usava um caminho incorreto para o ADB:
```python
# ERRADO
os.pat
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]