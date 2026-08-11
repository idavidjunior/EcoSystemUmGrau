---
tipo: aprendizado
tags: [vis-network, uso-real, mtime, atividade, tamanho, pythonw, windows, processo-gui]
data: 2026-08-04
contexto: Implementar "tamanho por uso real" no grafo do conhecimento (nós quentes vs frios) e corrigir terminal python abrindo junto ao widget.
decisao: (1) Metrica de atividade: usar o mtime do arquivo .md de cada nota como proxy de uso real. atv = max(0, min(1, 1 - dias/90)), clamped em 0.12 (nunca some). Guardado em n['atv'] e injetado no node JS. (2) size combina grau + atividade: use_size = size*(0.75+0.5*atv); size = max(size, use_size). (3) JS: pulso viva escala com atv - pulso=(0.05+0.09*atv), sombra += (4+10*atv)*pulso -> nós quentes latejam e brilham mais. (4) Windows: processos GUI/daemon devem rodar com pythonw.exe, nunca python.exe (este anexa console/Terminal junto).
impacto: Grafo vira termômetro real do uso do vault (notas editadas recente latejam e crescem). Nenhum terminal aparece junto ao widget/bridge: ambos rodam como pythonw. Preflight 100% PASS. Memory #84.
---

# 2026-08-04: Tamanho por uso real + iniciar GUI com pythonw

## Metrica de atividade (atv)
- Fonte: `os.path.getmtime(f)` por arquivo `.md`.
- `dias = max(0, (agora - mtime)/86400)`
- `atv = max(0.12, min(1.0, 1.0 - dias/90.0))` -> hoje=~1, >90 dias=0.12.
- Adicionada ao nó no `extrair_nos` e serializado no node JS (`atv`).

## Tamanho combinado (gerar_html)
- `use_size = size * (0.75 + 0.5*atv)`
- `size = max(size, use_size)` (centralidade nunca reduz o mínimo).

## Pulso vivo proporcional à atividade (tick)
- `pulso = sin(...) * (0.05 + 0.09*atv)`
- `sombra += (4 + 10*atv) * pulso`
- Efeito: nós quentes (recém editados) batem com mais energia e brilho.

## LIÇÃO Windows: python vs pythonw
- `python.exe` em `Start-Process` abre um console junto.
- `pythonw.exe` roda totalmente silencioso (sem Terminal).
- Regra: **todo processo GUI/daemon de longa duração (bridge 8765, widget) deve
  ser iniciado com `pythonw.exe`**, ex:
  `Start-Process "C:\...\pythonw.exe" -ArgumentList "scripts\widget_grafo.py"`
- Comandos de verificação:
  - porta: `netstat -ano | findstr :8765`
  - processo: `Get-CimInstance Win32_Process -Filter "Name like 'python%'"`
- O bridge responde via WS 8765 (celular reconecta automaticamente).

## Conexoes

- [[cluster-hub-programacao]]