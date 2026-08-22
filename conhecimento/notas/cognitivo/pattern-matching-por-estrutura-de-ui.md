---
tags: [cognitivo, formularios, inputs, labels, repetidos, ui-recognition]
aliases: [Pattern matching por estrutura de UI]
date: 2026-08-22
---

# Pattern matching por estrutura de UI

**Dominio:** ui-recognition

Toda interface segue padroes reconheciveis: modais tem header+body+footer, tabelas tem thead+tbody, listas sao scrollaveis com items repetidos, formularios tem labels+inputs. Reconhecer o padrao estrutural e mais rapido que ler cada elemento individualmente

Digitalizar a tela em zonas: topo = header/nav, esquerda = sidebar/menu, centro = conteudo principal, direita = paineis auxiliares, fundo = modais/overlays. Saber onde procurar cada tipo de elemento reduz tempo de busca em 60%
## Conexoes

- [[cluster-hub-navegacao]]
- [[cognitivo-hub-cognitivo]]