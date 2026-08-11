---
tipo: decisao
tags: [bibliaestudocompleta, recursos, importacao, ui]
data: 2026-08-09
contexto: O botao +IMPORTAR deveria abrir o mesmo menu nas telas Home e Meus Recursos, com o mesmo nome.
decisao: Criado ResourceImportMenu (com.biblia.estudo.utils) como menu unico com 3 opcoes: Importar Arquivo (multiplo), Importar Pasta (arvore com nomes reais via importFolderTree) e Criar Pasta. Home e ResourcesActivity passaram a usar o mesmo menu; a tela de Recursos deixou de ter botao +Arquivo separado.
impacto: UX consistente entre Home e Recursos; menos duplicacao de codigo de menu; importacao de arquivos na tela de Recursos passou a aceitar multiplos.

## Conexoes

- [[cluster-hub-programacao]]