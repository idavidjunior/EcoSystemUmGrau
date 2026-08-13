---
tipo: padrao
tags: [organizacao, auditoria, rotina, vigilante, orfaos, gitignore, manutencao]
data: 2026-08-13
contexto: Fase 3 da organização do EcoSystemUmGrau. Após a limpeza manual
(fase 1: 30 órfãos para _legado; fase 2: 31 artefatos fora do git), era preciso
transformar a auditoria em rotina automática para a bagunça nunca mais se
acumular. Existia scripts/detect_smells.py (code smells via ruff/pylint/radon),
mas era outro assunto — não cobria órfãos nem artefatos rastreados.
decisao: Criado scripts/audit_triagem.py (100% stdlib) com dois detectores:
(1) scripts órfãos — varredura de referências em todo o repo excluindo
.git/node_modules/backups/target/build/_legado/logs efêmeros/auto-referências,
respeitando a lista PROTEGIDOS_EXTERNOS (watchdog_start.bat, guardian_start.bat,
vigilante.ps1, watchdog.ps1, grafico_widget.bat, persistencia.ps1) porque são
usados por atalhos do Startup e tarefas agendadas, invisíveis para grep;
(2) artefatos rastreados no git — git ls-files filtrando padrões (.log, __pycache__,
.bak, .npy, screenshots .png, saídas de teste), ignorando sub-repos incorporados
(Projetos/, ferramentas/, ler-runtime/, ai-agents/) que cuidam do próprio git, e
tratando shot_*.ps1 como ferramenta (não artefato). Modo --fix move órfãos
confirmados para _legado via git mv (reversível, nunca apaga); artefatos do git
só são reportados (decisão humana). Integrado ao vigilante.ps1 como TRIAGEM
TIMER diário (roda --fix 1x/dia, loga movidos e artefatos pendentes).
Lição de teste: ao validar, descobri falsos positivos — test_vox.py e
ler-runtime/tests/* são testes LEGÍTIMOS (não lixo), e shot_clean/colors/full.ps1
são ferramentas de screenshot (não imagens). Refinado com extensão .png e
exclusão de sub-repos. Testado com arquivo órfão sintético: detectou e moveu.
Resultado: audit_triagem.py reporta "nenhum órfão, nenhum artefato", vigilante
reiniciado (PID novo) carregando o timer, test-ecosystem 32/32 PASS.
evidencia: scripts/audit_triagem.py; bloco TRIAGEM TIMER em vigilante.ps1;
teste sintético de --fix; test-ecosystem.ps1 32 PASS.
