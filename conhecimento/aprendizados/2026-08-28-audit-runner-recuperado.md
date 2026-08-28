---
tipo: erro
tags: [guardian, auditoria, monitor, audit_runner, widget]
data: 2026-08-28
contexto: system_guardian.py executava scripts/audit_runner.py a cada ~30 min para gerar runtime/audit_result.json e reportar saúde do ecossistema.
decisao: Recriar scripts/audit_runner.py (arquivo referenciado não existia mais), reutilizando audit_eco.run_audit como fonte única e escrevendo o resultado com escrita atômica (tmp + os.replace) no contrato que o guardian lê (timestamp epoch + score + findings).
impacto: Monitor de auditoria voltou a responder (resultado parado desde 21/08, guardian logando "resultado antigo"). Primeira execução: score 90/100, 2 erros (narrador_desktop não rodando; Cerebro Vivo sem ler tema) e 17 warnings, em grande parte por drift: as checagens da auditoria ainda referenciam widget_controle_jarvis.py enquanto o atual é widget_edge.py, e há duplicação de widgets (widget_edge, widget_grafo, widget_grafo_fixed). Pendências para evolução progressiva: atualizar checagens do audit_eco para o widget_edge, agendar limpeza_disco (hoje manual), consolidar widgets duplicados.

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]