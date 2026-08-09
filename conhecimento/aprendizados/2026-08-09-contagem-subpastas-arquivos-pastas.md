---
tipo: padrao
tags: [bibliaestudocompleta, recursos, ui, contagem]
data: 2026-08-09
contexto: Usuario pediu para mostrar a quantidade de subpastas e arquivos dentro das pastas na tela Meus Recursos.
decisao: ResourceListAdapter recebe UserResourceDao e mostra detalhe "N subpastas • M arquivos" no subtitulo das pastas (referenciadas via countChildren, locais via countByFolder). Na raiz, pastas referenciadas sem filhos persistidos sao materializadas em background (importChildrenForFolder) para exibir contagem real.
impacto: Usuario ve quantos itens ha dentro de cada pasta sem abrir; contagens corretas mesmo para pastas importadas antes da arvore.
