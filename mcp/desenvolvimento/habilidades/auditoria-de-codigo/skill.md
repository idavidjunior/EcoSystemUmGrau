---
name: auditoria-de-codigo
description: Auditoria sistemática de código para encontrar e corrigir bugs. Use quando o usuário pedir para "auditar", "olhe a função X", "olhe/veja a barra/a tela/o controle Y", "teste cada controle", "encontre bugs", "escaneie o código", "o que está errado/acontecendo em Z". Aplica o pipeline de escaneamento por fluxo com verificação por ferramentas autoritativas e auto-evolui a partir dos aprendizados que registra a cada auditoria.
---

# Auditoria de Código (auto-evolutiva)

> FONTE ÚNICA: este arquivo é o canônico. Espelhado em
> `~/.claude/skills/auditoria-de-codigo/SKILL.md` (deploy do opencode).
> SEMPRE edite aqui e sincronize o espelho.

## Princípio central
Bugs são encontrados pelo **FLUXO**, não pela leitura linear do arquivo.
Mapeie como dados/estados/eventos fluem entre arquivos, componentes e
persistência; depois valide cada elo com ferramentas autoritativas.

## Gatilhos típicos
- "audite o código / a função X"
- "olhe a barra / o botão / o painel / o controle Y" (apontar um elemento de UI
  quase sempre significa: há um bug ali)
- "teste cada controle e você vai ver"
- "escaneie / encontre os bugs / o que está errado"

## Pipeline (5 fases)

### Fase 1 — Escanear por fluxo (não por arquivo)
1. Liste todos os pontos de interação do alvo: estados, eventos, listeners,
   funções chamadas, chaves de persistência.
2. Monte matrizes explícitas:
   - localStorage: `chave → quem grava → quem lê → status (ok/órfã)`
   - Eventos: `gatilho → handler → efeito colateral`
   - Funções: `origem → destino`
3. Identifique o **source of truth** (gerador vs artefato gerado; código vs dados).
4. Cace **estados órfãos** (gravados mas nunca lidos; lidos mas nunca gravados).

### Fase 2 — Verificar com ferramentas autoritativas (nunca confiar no display)
- Leitura/display de arquivos pode corromper, truncar ou duplicar conteúdo.
- Ferramentas que não mentem: `py_compile`, `node --check`, contagens regex,
  **bytes hex crus**.
- `node --check` em HTML inline: extraia CADA bloco `<script>` isolado
  (regex non-greedy) e valide um a um — não o documento inteiro.
- Encoding: só afirme mojibake após comparar bytes hex.
  Ex.: `E2 80 94` = em-dash correto; `C3 A2 E2 82 AC E2 80 9C` = duplo-encode.

### Fase 3 — Corrigir no fonte, nunca no artefato
- Edite o gerador/origem, rode o build, revalide o artefato. O artefato gerado
  é sombra do fonte.

### Fase 4 — Rastrear dado vs código
- Quando um sintoma persistir após corrigir o código, rastreie UMA ocorrência até
  a origem (arquivo, nota, dataset). Se for dado ruim (ex.: mojibake no vault),
  não é bug do código — separe e reporte.

### Fase 5 — Pensar efeitos colaterais
- Cada correção contra o resto: restore vs inicialização, reset vs defaults,
  toggle de UI vs layout dependente, `!important` vs estilo inline, timing de
  animações (ex.: fit programático não dispara eventos de zoom).

## Auto-evolução com portão de qualidade (OBRIGATÓRIA ao final de CADA auditoria)

O cérebro da skill é `mcp/desenvolvimento/habilidades/auditoria-de-codigo/evolucao.py`
(rodar da raiz do repo ou via `python mcp/desenvolvimento/habilidades/auditoria-de-codigo/evolucao.py`).
Ele aplica gates anti-lixo ANTES de qualquer aprendizado entrar na skill:

1. **`evolucao.py add "<título>" "<lição>" --tipo <padrao|erro|episodio> --evidencia <caminho>`**
   - **Evidência obrigatória**: o caminho do arquivo onde o bug/padrão foi encontrado
     deve existir. Sem evidência → rejeitado (vai para `rejeitados.json` com o motivo).
   - **Dedup por similaridade**: se ≈ duplicado (similaridade ≥ 0.80), NÃO duplica —
     incrementa `recorrencias` do padrão existente.
   - **Acionabilidade**: lição sem ação prática é marcada como observação e NÃO vira
     regra no checklist até recorrer.
   - **Anti-overfitting**: padrão único só vira armadilha se impacto `alto`.
   - Ao ser aceito, registra no ecossistema via `memory_engine.py add` (loop fechado).
2. **`evolucao.py review`** — quando ≥3 padrões elegíveis acumulam (acionáveis,
   não no checklist, com ≥2 ocorrências OU impacto alto), absorve-os no checklist do
   próprio SKILL.md (com backup `skill.md.bak` + registro em `evolucao.md`).
3. **`evolucao.py stats`** — painel: aceitos/rejeitados/duplicados/elegíveis/revisões.
4. **`evolucao.py prune --dias 90`** — limpeza periódica: remove rejeitados antigos e
   padrões mortos (nunca os que já estão no checklist).
5. Além do script, crie/atualize `conhecimento/aprendizados/AAAA-MM-DD-<slug>.md`
   (contexto → decisão → implementação → lições) e registre na memória episódica.
6. **Após um `review`**: sincronize o espelho `~/.claude/skills/auditoria-de-codigo/SKILL.md`
   com o canônico (FONTE ÚNICA).

## Checklist de armadilhas conhecidas (manter atualizado via auto-evolução)
- [ ] Saída corrompida/duplicada na leitura → validar com ferramenta autoritativa.
- [ ] Estado órfão em localStorage (gravado/nunca lido ou lido/nunca gravado).
- [ ] Mojibake duplo-encoded em strings visíveis (confirmar em bytes hex).
- [ ] Editar artefato gerado em vez do gerador.
- [ ] Dado ruim vindo de fonte externa (vault/notas) confundido com bug de código.
- [ ] Correção que quebra restore/inicialização (timing, ordem de chamadas).
- [ ] Correção que ignora reset/defaults de persistência.
- [ ] Correção CSS anulada por `!important` (ou o contrário).
