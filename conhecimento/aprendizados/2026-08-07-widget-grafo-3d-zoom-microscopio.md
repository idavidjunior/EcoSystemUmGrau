---
tipo: padrao
tags: [grafo, widget, 3D, zoom-microscopio, correcao-bugs, vis-network, pythonw, geometria]
data: 2026-08-07
contexto: Iteração completa de refinamento do widget desktop "Cerebro Vivo" após feedback: piscar constante, botões 3D/Flash inúteis, pseudo-3D imperceptível, zoom-microscópio sem expansão fokal, controles não aparecendo.
decisao: Corrigir 6 bugs + implementar zoom microscópio com expansão focal real + forçar geometria visível.
impacto: Widget estável (sem reload infinito), efeito 3D perceptível, clique expande vizinhança em espiral, controles visíveis na tela principal.
---

# Widget Grafo — Correção Completa + Zoom Microscópio Focal + Geometria Visível (2026-08-07)

## Bugs Corrigidos

1. **Loop de reload infinito (pisca e reseta)** — `scripts/widget_grafo.py:_versao()`
   - Monitorava `rglob('*')` em `conhecimento/*` → capturava `cluster_mapper.json` (reescrito a cada geração)
   - Cada regenerar mudava mtime → versão mudava → API_INJECT recarregava a cada 2s
   - **Fix**: `rglob('*.md')` — só observa notas markdown reais

2. **Typo `pulsoForza` → `pulsoForca`** — `scripts/generate-graph-html.py` (3 temas)
   - Variável global é `_pulsoForca` (com "ç"), temas definem `pulsoForza` (com "z")
   - `aplicarTema()` fazia `t.pulsoForza` = `undefined` → pulsos sempre 0
   - **Fix**: corrigido em Neon, Glow, Calm (linhas 1622, 1636, 1651)

3. **Efeito 3D imperceptível** — `scripts/generate-graph-html.py:_zVivo()`
   - Amplitude onda viajante 0.26 → aumentada para **0.45** quando `_modo3D=true`
   - `_toggle3D` força `_tickPausado = false` para recalculo imediato

4. **Botão Flash duplicado** — `scripts/widget_grafo.py:WIDGET_JS_EXTRA`
   - `btnFlash` criado 2x no painel → conflito
   - **Fix**: unificado — criado uma vez, anexado ao grupo3D

5. **Botão 3D sem feedback visual** — `scripts/widget_grafo.py`
   - **Fix**: `box-shadow` glow quando ativo (LED visual claro)

6. **Sintaxe JS quebrada em `_expandirFoco`** — `scripts/generate-graph-html.py`
   - f-string gerou `}});` → `})` sem fechar `if` interno → `SyntaxError: Unexpected token ')'`
   - Widget travava no boot, grafo sumia
   - **Fix**: `}}` extra para fechar `if` antes de `}});` do `forEach`
   - **Lição**: validar JS do HTML gerado com esprima após alterações no template

7. **Controles não apareciam** — geometria salva em posição fora da tela
   - Geometria `x=556, y=33` → pode estar em monitor secundário/fora da tela visível
   - Widget `pythonw` abre invisível se geometria fora da tela
   - **Fix**: força geometria para `x=100, y=100, width=1024, height=768` (tela principal)
   - Agora `pythonw` abre visível corretamente

## Zoom Microscópio com Expansão Focal (NOVO)

Implementado em `scripts/generate-graph-html.py:_expandirFoco(id, corGrupo)`:

- **Clique num nó**: nó central cresce 2x (+24px) com glow forte
- **Vizinhos diretos (1 hop)**: se espacam em espiral (raio +28px), giram angularmente, crescem +4px
- **Vizinhos de 2º (2 hop)**: crescem levemente (+3px)
- **Resto dos nós**: escurecem para `#14141f`, opacity 0.06
- **Arestas**: do foco brilham (width=4, opacity=1); outras desaparecem (opacity=0.05)
- **Zoom focal**: `network.focus(id, {scale: 0.9})` animado
- **Animação**: 20 frames × 16ms ≈ 320ms suave
- Integração: `flashNo` + `_destacado` — `limpar()`/`Home` reseta tudo

## Como Usar

```bash
# Produção (sem console)
widget-grafo.bat
# ou
pythonw scripts/widget_grafo.py

# Debug (com console + devtools)
python scripts/widget_grafo.py
```

**Controles (canto superior direito)**:
- Botão 3D (🐍/★): alterna onda viajante ampla (0.45 vs 0.26) + glow visual
- Botão Flash (⚡): alterna brilho no clique + glow visual  
- Slider Velocidade (0.25x-3x): multiplica ondas/pulsos/física
- Slider Órbita (0-3x): amplitude deriva orbital
- Slider Intensidade 3D (0-3x): força onda viajante
- Select Tamanho: Compacto/Média/Padrão/Grande/Máxima → `pywebview.api.redimensionar()`
- Select Tema: Neon/Glow/Calmo/Padrão → cores + física calibrada
- Botão T (etiquetas): toggle labels on/off
- Botão M (☰/…): toggle menu lateral
- Botão Reset (↺): limpa preferências localStorage
- Botão Olho (👁/👁️): mostra/esconde painel
- Busca: filtro por palavra no grafo (data-filter="txt")

**Interações**:
- Clique num nó → zoom microscópio + expansão focal
- Clique direito → toggle visibilidade header/legenda
- Home → restaura visão inicial
- Limpar → remove todos os destaques

## Validação

- **0 erros JS** (esprima: 6 blocos no HTML gerado)
- `python -m py_compile` OK
- `preflight_check.py` OK
- Widget testado: `pythonw` (produção) + `python debug=True` (devtools)
- Geometria forçada: `x=100, y=100, w=1024, h=768` → visível no monitor principal
- HTTP server interno pywebview: porta aleatória (~42400), serve `docs/grafo_widget.html`

## Conexões

- [[2026-08-06-widget-grafo-correcao-bugs-e-teste-completo]] — correções anteriores (TDZ, chaves duplas)
- [[2026-08-05-fisica-animacao-grafo-orbital]] — deriva orbital
- [[2026-08-04-widget-grafo-turbinado]] — controles velocidade, tooltips, temas

## Conexoes

- [[cluster-hub-programacao]]