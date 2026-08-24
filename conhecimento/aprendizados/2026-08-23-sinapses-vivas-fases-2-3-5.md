---
tipo: padrao
tags: [sinapses-vivas, memoria, plasticidade, runtime]
data: 2026-08-23
contexto: Projeto Sinapses Vivas — o cérebro vivo precisava evoluir pelo uso, não apenas mudar por edição manual.
decisao: Implementadas as fases 2, 3 e 5 sobre a base das fases 0-1. Arestas de co-uso (runtime/sinapses/arestas.json) agora são expostas no contexto via _carregar_sinapses_dinamicas; o vigilante ganhou sinapsesTimer 24h que roda "sinapses.py ciclo" (decay + reindexação + relatório de saúde), substituindo e removendo o decayTimer antigo; detectar_lacuna registra em lacunas.jsonl quando o contexto sai raso (score máximo < 3.0); memórias com epistemic_status=inferido são promovidas a confirmado quando servem uma tarefa fechada como boa.
impacto: A memória do ecossistema agora tem ciclo completo de plasticidade — nasce, é usada, é reforçada ou enfraquecida, cria laços emergentes com vizinhas, decai se ignorada, sinaliza lacuna e sobe de status epistêmico por evidência real. Bug KeyError access_count corrigido em reinforce/penalizar (default seguro via m.get).
---

# Sinapses Vivas — Fases 2, 3 e 5

## O que foi feito

Fase 2 (arestas emergentes): `_carregar_sinapses_dinamicas` lê arestas.json, coleta
vizinhos das memórias servidas, ordena por peso acumulado e injeta até 4 no
contexto como `sinapses_dinamicas`, renderizadas como "Sinapses vivas
(co-uso real, peso)". Prova: consulta sobre benchmark trouxe 481/482/484 com peso 4.

Fase 3 (ciclo de vida): `sinapses.py ciclo` executa decay_pass (com nova guarda:
decisão consolidada confidence>=0.9 nunca arquiva por idade), reindexação semântica
e grava relatorio_saude.txt atomicamente. No vigilante.ps1, o decayTimer diário foi
REMOVIDO (descontinuação explícita) e substituído pelo sinapsesTimer (24h) —
evitou decay rodar 2x/dia.

Fase 5 (autonomia): `sinapses.py lacuna` mede o score máximo da última telemetria;
abaixo de 3.0 grava registro em lacunas.jsonl e imprime LACUNA_DETECADA para o
agente agir (busca-web/scrape-md → destilar). `_promover_inferidas` sobe
epistemic_status inferido→confirmado quando a memória serviu tarefa boa,
registrando confirmado_por=tarefa_boa_sinapses.

## Bugs encontrados pelos testes adversariais

- reinforce() fazia m['access_count'] += 1 e quebrava com KeyError em memórias
  antigas sem o campo — corrigido com m.get('access_count', 0) em reinforce E
  penalizar.
- Primeira tentativa de editar o render quebrou indentação (for/if duplicado);
  py_compile pegou na hora.

## Lições

- Teste adversarial com memória sintética sem campos padrão revelou bug que
  afetaria memórias reais antigas.
- Verificar rotinas existentes antes de adicionar timers novos: quase dupliquei
  o decay diário; a cláusula anti-duplicação mandou consolidar removendo o velho.

## Estado final

Preflight técnico (10/10 PASS) e ético passaram. Memória #498 registra o marco.
Pendência futura: vigiar primeira execução do sinapsesTimer no próximo boot do
vigilante; fase de destilação automática (coleta web → memória) permanece
orquestrada pelo agente na sessão, não autônoma silenciosa.
