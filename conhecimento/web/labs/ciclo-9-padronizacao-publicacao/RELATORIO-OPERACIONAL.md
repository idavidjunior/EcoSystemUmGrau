# Relatório Operacional — Ciclo 9: Padronização e Publicação

Categoria: episodio
Fonte: Missão permanente de capacitação web — Ciclo 9
Projeto: EcoSystemUmGrau
Dominio: Engenharia Web — bloco K

## MISSION
Entregar o modo de construir, rodar e publicar a trilha web de forma
reproduzível: um único comando que valida todos os labs determinísticos,
um runbook de operação web documentando a stack inteira, e um pipeline de
CI no pipe existente (GitHub Actions). Rodar um lab não pode depender de
memória do operador — o script e o runbook devem bastar.

## STATUS
Concluído e consolidado em 2026-09-10. Evidência: `run_suite.py` executado
localmente com 5 labs aprovados e 0 falhas; CI web criado em
`.github/workflows/web-ci.yml`; runbook de operação publicado em
`conhecimento/web/RUNBOOK-OPERACAO-WEB.md`.

## ENTREGAS
- `conhecimento/web/run_suite.py`: build/run script reproduzível. Roda cada
  `test_*.py` no próprio diretório (imports relativos), sobe e derruba o
  servidor do Ciclo 6 sozinho (o teste dele não é auto-contido), agrega
  PASS/FAIL por lab e grava `benchmarks/ciclo-9-run-suite.json`. Modo padrão
  = determinístico (sem IA/playwright); `--tudo` inclui Ciclos 4, 7 e 8.
- `conhecimento/web/RUNBOOK-OPERACAO-WEB.md`: runbook de operação web — a
  entrega principal. Cobre stack, como rodar cada lab, como subir o produto
  do Ciclo 8, como medir CWV, troubleshooting, e como o CI funciona.
- `.github/workflows/web-ci.yml`: CI determinístico no pipe existente
  (GitHub Actions), Python 3.12, executa `run_suite.py` em cada push/PR.
- `adrs/2026-09-10-adr-009-padronizacao-publicacao.md`: ADR-009 com a
  decisão de padronização/publicação.
- Roadmap bloco K atualizado: UNDERSTOOD/2 → VALIDATED/3.
- Aprendizado do Ciclo 9 consolidado.

## TESTES EXECUTADOS
python conhecimento/web/run_suite.py
-> STATUS: OK (5 labs aprovados: Ciclos 1, 2, 3, 5, 6 — 0 falhas, 0 skips).
   Ciclo 6 validado com servidor orquestrado pelo próprio script.

## EVIDÊNCIAS
- `benchmarks/ciclo-9-run-suite.json` gerado automaticamente pelo script.
- Mapa K -> VALIDATED/3 (CI + script reproduzível + runbook).

## FALHAS ENCONTRADAS
- Primeira versão do `run_suite.py` exigia o marcador literal "STATUS: OK"
  na saída do lab; o Ciclo 1 não imprime esse marcador (usa exit code), o
  que gerava falso FAIL. Corrigido: sucesso decidido pelo returncode.
- O filtro do escopo padrão incluía inicialmente labs de IA/playwright
  (Ciclos 4/7/8) por engano; corrigido para só rodar os determinísticos.
- O teste do Ciclo 6 não é self-contained (precisa de servidor de pé);
  descoberta documentada — o orquestrador cuida do ciclo de vida do server.

## RISCOS E DEPENDÊNCIAS
- `websockets` e `httpx` precisam estar instalados no ambiente de CI
  (declarados no workflow web-ci.yml).
- `run_suite.py --tudo` depende de chaves de IA e de playwright instalado;
  fica no escopo local, fora do CI determinístico.
- Docker (bloco K) segue ausente; CI via GitHub Actions cobre o requisito
  de pipeline, conforme decisão do ADR-009.

## PRÓXIMA AÇÃO
Bloco L (arquitetura) e Iteração 2: Node/npm ausente bloqueia B/C/Next;
Docker ausente restringe K ao pipe existente. Revisitar quando o ambiente
de Node estiver disponível.