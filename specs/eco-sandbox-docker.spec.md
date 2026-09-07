---
id: spec-eco-sandbox-docker
versao: 0.1.0
status: ativa
componente: scripts/eco_sandbox.py
tags: [sandbox, docker, seguranca, isolamento, agentes]
data: 2026-09-07
---

# Spec — Sandbox Isolado (Docker)

## Objetivo

O sandbox isolado executa código de agentes dentro de container Docker com limites rígidos, servindo de base segura para tudo que vem depois.

## Requisitos

1. O cliente vive em `scripts/eco_sandbox.py` e expõe `executar(codigo, linguagem)` com retorno em dicionário.
2. O cliente prefere Docker quando disponível e cai para execução local restrita quando Docker está ausente.
3. A imagem de execução usa multi-stage com base enxuta, usuário não-root e entrypoint explícito.
4. Cada execução roda com rede desabilitada por padrão, com liberação explícita por chamada.
5. Cada execução respeita teto de tempo, memória, CPU, processos, disco e tamanho de saída.
6. O workspace do container é efêmero com montagem somente leitura do código e escrita só em diretório temporário.
7. Todo código passa por validação do `security_engine` antes de executar, com bloqueio de injection e path traversal.
8. Nenhum segredo do host é copiado para a imagem ou montado no container em nenhuma hipótese.
9. Cada execução gera auditoria estruturada com comando, limites, duração, saída resumida e motivo de bloqueio.
10. O EcoClient ganha método opcional que delega execução ao sandbox, sem mudar a interface existente.

## Restrições

- Windows com Docker Desktop opcional, com degradação graciosa quando Docker está ausente.
- Cliente em Python com apenas biblioteca padrão, sem dependência nova no runtime.
- Imagem sem `latest` em produção, com versão travada e `.dockerignore` rigoroso.
- Commit e push continuam exclusivos do gate de persistência, nunca dentro do sandbox.
- Logs em stdout e stderr com redação de segredos antes de persistir.
- Respeito às cláusulas de ponto único de persistência, idioma pt-BR e deveres externos.

## Dependências

- `scripts/security_engine.py` — validação de entrada, comandos e `SandboxConfig` como referência de limites.
- `scripts/eco_client.py` — ponto de integração programática que delega ao sandbox.
- `scripts/tool_orchestrator.py` — fila de execução com timeout e circuit breaker como chamador futuro.
- `Projetos/TradingAgents/Dockerfile` — padrão existente de multi-stage com usuário não-root.
- `Projetos/claude-code-extra-agents/skills/docker-patterns/skill.md` — checklist de build seguro e reproduzível.
- Docker Desktop como provedor de isolamento quando instalado no host.

## Premissas

- Docker pode estar ausente no host e o cliente continua operando em modo degradado.
- O host é Windows com PowerShell 5.1 e Python 3 disponível no PATH.
- O código de agentes é tratado como não confiável até prova em contrário.
- A rede do container nasce desligada e só liga com autorização explícita por execução.
- Os limites padrão espelham o `SandboxConfig` atual com teto de 60 segundos por execução.

## Entradas e Saídas

- Entrada: código fonte em texto, linguagem suportada, limites opcionais e flag explícita de rede.
- Saída: dicionário com `ok`, saída padrão, saída de erro, duração, limites aplicados e motivo de falha.
- Efeito colateral: container efêmero criado e destruído, auditoria registrada e diretório temporário limpo.

## Casos de Borda

- Docker ausente: retorna modo degradado com execução local restrita e alerta registrado.
- Tempo esgotado: mata o container e retorna timeout com saída parcial resumida.
- Memória estourada: encerra com falha controlada sem afetar o host.
- Código vazio: rejeita antes de criar container, sem erro interno.
- Comando bloqueado: validador veta antes da execução com motivo explícito.
- Imagem ausente: tenta build local uma vez e falha com motivo claro se não concluir.
- Saída gigante: trunca com marcação e preserva o início e o fim.

## Critérios de Aceitação

- [arquivo:specs/eco-sandbox-docker.spec.md] Spec existe e é o documento desta entrega.
- [arquivo:scripts/security_engine.py] Motor de segurança referenciado existe.
- [comando:python -c "import ast; ast.parse(open('scripts/security_engine.py',encoding='utf-8').read())"] Motor de segurança continua com sintaxe válida.
- Critério manual: com Docker instalado, um script de agente executa via sandbox sem tocar no host.
- Critério manual: sem Docker instalado, o cliente retorna degradado com alerta em vez de travar.
- Critério manual: nenhuma mudança visual ou de interface acompanha a entrega do sandbox.

## Definition of Done

- [ ] Cliente implementado em `scripts/eco_sandbox.py` conforme os requisitos.
- [ ] Imagem de execução com Dockerfile multi-stage, não-root e `.dockerignore`.
- [ ] Integração opcional via EcoClient sem quebrar a API existente.
- [ ] Evidências: execução isolada e modo degradado demonstrados em log.
- [ ] Código versionado no git via gate (`persistencia.ps1`).

## Riscos

- Docker ausente no host atual — severidade alta (mitigado por modo degradado com execução local restrita).
- Fuga de container por montagem indevida — severidade alta (mitigado por montagem somente leitura e escrita só em temporário).
- Vazamento de segredo na imagem — severidade alta (mitigado por proibição de copiar segredos e scan no build).
- Estouro de recursos travando o host — severidade média (mitigado por tetos de CPU, memória, disco e timeout).
- Complexidade excessiva antes da necessidade — severidade média (mitigado por API mínima com um método principal).

## Testes Relacionados

- scripts/security_engine.py
- scripts/eco_client.py
- scripts/test_eco_client.py
