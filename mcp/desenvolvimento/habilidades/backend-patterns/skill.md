---
name: backend-patterns
description: |
  Padr�es backend para servi�os resilientes: contratos claros, separa��o de camadas, observabilidade e confiabilidade.
  Trigger phrases: "backend architecture", "service layer", "repository pattern", "API backend"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Backend Patterns � Servi�os Confi�veis

## Objetivo
Projetar servi�os leg�veis e resilientes com baixo acoplamento e alta testabilidade.

## Pré-requisitos (carregar antes)
- `fundamentos-computacao` — Syscalls, memory model, network stack (TCP/IP, sockets, epoll/io_uring), file I/O (mmap, sendfile, splice), process/thread model, virtual memory, ELF linking — base para arquitetura de camadas, observabilidade, contratos, deployment

## Estrutura sugerida
- Camada de apresenta��o (HTTP/transport)
- Camada de aplica��o (casos de uso)
- Camada de dom�nio (regras centrais)
- Camada de infraestrutura (DB, filas, APIs externas)

## Pilares t�cnicos
- Contratos expl�citos (DTOs, schemas, versionamento)
- Idempot�ncia em opera��es cr�ticas
- Controle de concorr�ncia e retry seguro
- Observabilidade por default (logs, m�tricas, traces)

## Checklist operacional
- Timeouts e circuit breaker definidos?
- Erros mapeados para c�digos coerentes?
- Queries cr�ticas indexadas e paginadas?
- Segredos fora do c�digo?
- Runbook de incidente dispon�vel?

## Testes essenciais
- Unit para regras de dom�nio
- Integration para DB/externos
- Contract tests entre servi�os
- Testes de carga b�sicos em endpoints cr�ticos

## Anti-patterns
- L�gica de neg�cio no controller
- Depend�ncia circular entre m�dulos
- Retries sem limite e sem jitter
- Erros gen�ricos sem contexto

## Sa�da esperada do agente
- Diagrama de camadas e responsabilidades
- Padr�o de erro e observabilidade
- Matriz de riscos t�cnicos
- Plano de testes por camada