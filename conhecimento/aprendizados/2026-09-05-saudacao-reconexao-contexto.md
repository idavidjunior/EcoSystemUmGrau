---
tipo: padrao
tags: [jarvis-bridge, saudacao, reconexao, contexto, historico]
data: 2026-09-05
contexto: O VoxUmGrau (app Android + jarvis_bridge.py) retomava a cada reconexão um
 diagnóstico adb antigo, mesmo depois de a tarefa estar encerrada. Sintoma: cada
 queda → saudação de retomada citando "diagnóstico adb".
decisao: Causa raiz = (1) saudação de reconexão usava _contexto_recente() com 7 pares
 (últimas 14 linhas), ancorando em bloco antigo de diagnóstico inconcluso; (2) a
 instrução do prompt dizia para "retomar naturalmente o assunto em curso", incentivando
 a LLM a tratar tarefa antiga como ativa; (3) o histórico real (conversa_unica.json,
 raiz) continha o bloco truncado do diagnóstico adb ainda presente na cauda.
 Correcao aplicada: _contexto_recente(pares=2) no saudar() de reconexão; instrução
 explícita para NÃO retomar/citar tarefa antiga se as últimas interações forem
 despedida ou pedido fechado; poda do histórico removendo as linhas 98-131 (bloco do
 diagnóstico ADB e duplicatas "do AD"), com backup conversa_unica.json.bak-20260905.
impacto: Saudaçoes de reconexão passam a focar apenas nas últimas 2 trocas reais;
 histórico limpo de ruído; py_compile OK.
