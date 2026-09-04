---
tipo: erro
tags: [maestro, runtime, resiliencia, pid, heartbeat]
data: 2026-09-04
contexto: O livro do Maestro mantinha serviços mortos e o PID persistido do daemon apontava para processo inexistente.
decisão: Reconciliar por PID e heartbeat, iniciar o daemon automaticamente com lock único e executar a autocura no boot completo.
impacto: Registros órfãos deixam de bloquear reinícios, o status informa a vida real do processo e clientes recuperam o Maestro sem intervenção manual.
---

O livro não pode confiar no campo vivo nem na existência do arquivo PID. A reconciliação usa psutil e marca pid_morto ou heartbeat_obsoleto. O cliente usa um lock de inicialização para evitar dois daemons concorrentes. O boot completo chama garantir_maestro; --check permanece somente verificação.

Validação: dez testes do Maestro, boot íntegro e diagnósticos estáticos sem erros.
