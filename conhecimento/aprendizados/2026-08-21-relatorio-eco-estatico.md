---
tipo: padrao
tags: [dashboard, relatorio, html-estatico, stdlib, hsc, integridade]
data: 2026-08-21
contexto: Usuário pediu visão tipo PowerBI das informações do eco sem peso adicional
decisao: Relatório HTML estático autocontido gerado sob demanda por script stdlib; zero processo residente, zero porta, zero dependência.
impacto: scripts/relatorio_eco.py gera runtime/relatorios/relatorio_eco.html (~13KB) com fidelidade HSC, checks, conflitos, memórias por tipo, pendências e auditoria de integridade.
---

# Relatório Eco estático — lições

## Decisão
PowerBI/Grafana/Metabase seriam delírio para este ecossistema (licença, Docker,
banco, processo residente que o system_guardian mataria em pico de RAM). O mesmo
valor se obtém com um arquivo HTML autocontido: dados embutidos em
window.ECO_DADOS, gráficos canvas vanilla, abre offline via file://.

## Erros cometidos e corrigidos na implementação
1. Placeholder duplicado: template tinha `window.__DADOS__=__DADOS__` e o replace
   do payload corrompia o próprio token. Correção: tokens distintos (%%PAYLOAD%%).
2. Coletor de integridade montava a lista de problemas mas nunca a devolvia
   (variável local). Correção: retornar "_problemas" no dict e pop() no main.
3. Payload embutido precisa escapar "</" → "<\/" ou um "</script>" dentro de
   qualquer texto quebraria a página.

## Padrão estabelecido
Coleção tolerante a ausência (try/except → default vazio), agregações calculadas
em Python, renderização em JS puro. Adversarial validado: sem runtime/hsc e sem
memories.json o relatório gera degradado (zeros/None) sem crash.

## Achado real
O relatório revelou registro de memória #193 corrompido: campo kind contém uma
frase inteira (bug antigo do memory_engine com argumentos deslocados). Pendente
consertar esse registro no memories.json.
