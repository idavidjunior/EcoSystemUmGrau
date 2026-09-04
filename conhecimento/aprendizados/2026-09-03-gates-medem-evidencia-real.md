---
tipo: erro
tags: [auditoria, gates, constituicao, enforcement]
data: 2026-09-03
contexto: Auditoria crítica da Constituição do EcoSystemUmGrau.
---

# Gates devem medir evidência real

## Decisão
Gates de conformidade devem usar código de saída, execução registrada e critérios bloqueantes. Mensagens de commit, estados administrativos e heurísticas não bastam como prova de execução.

## Implementação
A Constituição recebeu uma hierarquia explícita. O Kernel passou a chamar o validador de idioma. A auditoria passou a reprovar sincronizações registradas sem sucesso. O preflight ético deixou de tratar o modo desativado como aprovação.

## Impacto
A auditoria agora pode reprovar uma entrega mesmo quando o score agregado parece alto. Fixtures e logs continuam visíveis como alertas, sem serem confundidos com código de produção.

## Pendência
Seis registros históricos de @sync ainda estão sem sucesso. Eles permanecem como falha até uma sincronização real ser executada.
