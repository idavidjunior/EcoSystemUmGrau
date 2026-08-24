---
tipo: padrao
tags: [visual, html, ferramenta, preferencia-usuario, mockup]
data: 2026-08-24
contexto: David pediu que informacoes e mockups fossem materializados em arquivo HTML temporario quando ele pedir "visual", sem janelas nem navegador, com opcao de salvar como template
decisao: Criado scripts/gerador_visual.py (100% stdlib, escrita atomica) com 5 tipos de renderizacao; padrao registrado na memoria #510
impacto: Qualquer agente do ecossistema pode materializar dados em visual HTML com um comando; sem servidor, sem navegador, so o arquivo
---

# Gerador de visuais temporarios (gerador_visual.py)

## Justificativa da criacao
Inventario verificado antes: relatorio_eco.py tem template fixo de relatorio;
dashboard_http.py e run_dashboard.py sao servidores HTTP; generate-graph-html.py
e especifico de grafos. Nenhum gerava arquivo visual generico temporario.
Necessidade real expressada pelo usuario, sem equivalente.

## Uso
python scripts/gerador_visual.py --titulo "..." --tipo kpi|tabela|barras|mockup|texto --arquivo dados.json
Ou --json inline. --salvar caminho.html para persistir como template.

## Contrato
Saida default: %TEMP%\opencode\visuals\<tipo>_<timestamp>.html
Nunca abre navegador nem servidor. Escrita atomica (tmp + os.replace).
HTML autocontido, UTF-8, CSS embutido, tema escuro.

## Testes executados (2026-08-24)
Quatro tipos gerados com sucesso (kpi, tabela, barras, mockup), arquivos
verificados quanto a codificacao e estrutura.
