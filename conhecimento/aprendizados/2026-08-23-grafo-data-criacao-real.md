# Grafo usa data de criação real do conhecimento

## Contexto
O pulso amarelo "sinapses novas" do Cerebro Vivo acendia ~575 notas antigas após regeneração do vault, porque usava mtime dos arquivos (atualizado em massa pelo gerador) e não a data real de criação do conhecimento.

## Decisão
Cadeia de prioridade para a data de cada nota:
1. `created_at` explícito no item do grafo (`KGNode` já tinha o campo; `add_node` agora aceita e `learning_engine._persist_to_kg` repassa `record.created_at`)
2. Data embutida no título (regex `\d{4}-\d{2}-\d{2}`)
3. Primeiro commit git da nota (`git log --reverse --diff-filter=A`) — fonte verdadeira de criação
4. `last_updated` global / hoje como último recurso

Fluxo: gerador escreve `date:` no frontmatter → `widget_grafo.mapa_datas()` lê frontmatter (fallback mtime) → payload `tm` → pulso respeita janela configurável (AJUSTES.novaH).

## Impacto
- Só conhecimento genuinamente novo pulsa; notas antigas ficam com cor base.
- Janela, intensidade e brilho do pulso controláveis no painel Ajustes.
- Filtro "Sinapses novas" no painel Foco agora é confiável.

## Aprendizados técnicos
- Git escapa nomes com acento em octal por padrão: usar `-c core.quotepath=false` ao parsear `--name-only`.
- Cache `_mtimes`/payload em `runtime/cerebro_dados.json` pode mascarar rebuild: ao trocar a fonte de datas, apagar o arquivo e reiniciar o widget.
- `python -c` com aspas aninhadas quebra no PowerShell: preferir scripts temporários.
