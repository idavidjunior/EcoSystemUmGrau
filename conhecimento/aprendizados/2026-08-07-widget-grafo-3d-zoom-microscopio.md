---
tipo: padrao
tags: [grafo, widget, 3D, zoom-microscopio, correcao-bugs, vis-network]
data: 2026-08-07
contexto: Iteração de refinamento do widget desktop "Cerebro Vivo" após feedback do usuário: piscar constante, botões 3D/Flash inúteis, pseudo-3D imperceptível, zoom-microscópio sem expansão fokal.
decisao: Corrigir bugs 3D + implementar zoom microscópio com expansão focal real.
impacto: Widget volta a ficar estável (sem reload infinito), efeitos 3D torna-se perceptível, clique num nó expande a vizinhança em espiral (microscópio real).
---

# Widget Grafo — 3D visível + Zoom Microscópio com Expansão Focal (2026-08-07)

## Bugs Corrigidos

1. **Loop de reload infinito** (`scripts/widget_grafo.py` — `_versao()`)
   - A função monitorava `rglob('*')` em `conhecimento/*`, capturando `cluster_mapper.json` (reescrito em toda geração)
   - Cada regenerar mudava o mtime → versão mudava → API_INJECT recarregava a página a cada 2s → "pisca e reseta"
   - **Fix**: `rglob('*.md')` — só observa notas markdown reais (fonte viva)

2. **Typo `pulsoForza` → `pulsoForca`** (`scripts/generate-graph-html.py`)
   - Variável global é `_pulsoForca` (com "ç"), mas os temas Neon/Glow/Calm definiam `pulsoForza` (com "z")
   - O `aplicarTema()` fazia `t.pulsoForza` = `undefined` → pulsos de sinapse sempre 0
   - **Fix**: corrigido em 3 temas

3. **Efeito 3D imperceptível** (`scripts/generate-graph-html.py` — `_zVivo`)
   - A onda viajante (`viajante`) tinha amplitude 0.26 quando `_modo3D=true`
   - Era visível apenas com atenção, parecia "inútil"
   - **Fix**: amplitude aumentada para 0.45 quando `_modo3D=true`; `_toggle3D` agora força `_tickPausado = false` para recalculo imediato

4. **Botão Flash duplicado** (`scripts/widget_grafo.py`)
   - Criado `btnFlash` duas vezes no painel: uma no grupo 3D, outra no grupo dedicado
   - **Fix**: unificado — btnFlash criado uma só vez, anexado ao grupo3D

5. **Botão 3D sem feedback visual** (`scripts/widget_grafo.py` — `WIDGET_JS_EXTRA`)
   - O botão não mostrava estado ativo visualmente
   - **Fix**: `box-shadow` cintilante quando ativo (glow no botão)

## Zoom Microscópio com Expansão Focal

Implementado em `scripts/generate-graph-html.py` — função `_expandirFoco(id, corGrupo)`:

- **Clique num nó**: nó central **cresce 2x** +24px, com glow forte
- **Vizinhos diretos (1 hop)**: se **espacam em espiral** (raio +28px), giram angularmente, crescem +4px
- **Vizinhos de 2º (2 hop)**: crescem levemente
- **Resto dos nós**: escurecem para `#14141f`, opacity 0.06
- **Arestas**: do foco ficam `width=4 opacity=1`; outras caem para `opacity=0.05`
- **Zoom focal**: `network.focus(id, {scale: 0.9})` após animação (20 frames × 16ms ≈ 320ms)
- Integração com `flashNo` e `_destacado` — `limpar()`/`telaInicial()` reseta tudo

## Como Usar

```bash
python scripts/widget_grafo.py
# ou
widget-grafo.bat
```

Controles:
- Botão 3D (🐍/★): alterna onda viajante (ampliada 0.45 vs 0.26)
- Botão Flash (⚡): alterna efeito de brilho no clique
- Clique num nó: zoom microscópio + expansão focal
- Home: restaura visão inicial
- Limpar: remove todos os destaques

## Conexões

- [[2026-08-06-widget-grafo-correcao-bugs-e-teste-completo]] — correções anteriores (TDZ, chaves duplas, injetar scripts)
- [[2026-08-05-fisica-animacao-grafo-orbital]] — deriva orbital
- [[2026-08-04-widget-grafo-turbinado]] — controles de velocidade, tooltips

