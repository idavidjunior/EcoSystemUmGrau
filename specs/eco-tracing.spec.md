---
id: spec-eco-tracing
versao: 0.1.0
status: proposta
componente: scripts/eco_trace.py
tags: [tracing, observabilidade, langfuse, langsmith, gargalos]
data: 2026-09-07
---

# Spec — Tracing Integrado

## Objetivo

O tracing integrado registra o caminho de cada tarefa com tempos reais, revelando gargalos antes de escalar o ecossistema.

## Requisitos

1. O cliente vive em `scripts/eco_trace.py` e expõe `trace`, `span` e `finalizar` com retorno em dicionário.
2. Cada trace carrega id único com spans aninhados de nome, início, fim, atributos e eventos.
3. Os pontos iniciais são roteamento LLM, execução de ferramenta, disparo da agenda e sandbox.
4. O coletor local grava em `runtime/traces/` com rotação diária e teto de disco.
5. A exportação para Langfuse ou LangSmith é opcional e só liga com chave em variável de ambiente.
6. Sem chave configurada o sistema opera só local sem erro e sem perda de função.
7. A amostragem é configurável com cem por cento em erro e fração no caminho feliz.
8. Todo atributo passa por redação de segredos antes de gravar ou exportar.
9. O overhead do tracing fica abaixo de cinco por cento com escrita assíncrona em lote.
10. A CLI mostra resumo com caminho mais lento, erro dominante e gargalo por componente.

## Restrições

- Windows com Python 3 e HTTP só na exportação opcional, nunca no caminho local.
- Chave e segredo só via ambiente, nunca no código nem no trace gravado.
- Falha do backend externo nunca quebra a tarefa, só registra aviso degradado.
- Teto de disco local com descarte do mais antigo quando estourar o limite.
- Respeito às cláusulas de ponto único de persistência, idioma pt-BR e deveres externos.

## Dependências

- `scripts/llm_router.py` — roteamento com `_record_routing` como ponto de span LLM.
- `scripts/tool_orchestrator.py` — métricas e `ToolCall` como ponto de span de ferramenta.
- `scripts/eco_agenda.py` — disparos com id como ponto de span de agenda.
- `scripts/eco_sandbox.py` — auditoria de execução como ponto de span de sandbox.
- `scripts/memory_engine.py` — redação de segredos reaproveitada nos atributos.
- `requirements.txt` — `requests` e `httpx` já homologados para a exportação opcional.
- Langfuse ou LangSmith como backend externo opcional via chave em ambiente.

## Premissas

- Nenhuma integração externa de tracing existe hoje no ecossistema.
- O formato interno espelha spans OpenTelemetry sem exigir o SDK pesado.
- A exportação traduz o formato interno para a API de cada backend.
- O coletor local é a fonte de verdade e o backend é espelho descartável.
- O gargalo real aparece no percentil alto, não na média simples.

## Entradas e Saídas

- Entrada: nome do span, atributos, eventos e contexto pai opcional.
- Saída: dicionários com `ok`, ids criados e caminho de resumo por trace.
- Efeito colateral: arquivo local rotacionado e lote exportado quando habilitado.

## Casos de Borda

- Backend fora do ar: lote fica em fila local e tenta depois sem bloquear.
- Chave ausente: exportador desliga sozinho com aviso único por sessão.
- Disco no teto: apaga o dia mais antigo e segue gravando sem erro.
- Span sem fim por crash: próximo tick fecha com motivo órfão temporal.
- Atributo gigante: trunca com marcação preservando início e fim.
- Amostragem zerada em erro: erro sempre grava cem por cento mesmo assim.
- Relógio com salto: duração negativa vira zero com flag de correção.

## Critérios de Aceitação

- [arquivo:specs/eco-tracing.spec.md] Spec existe e é o documento desta entrega.
- [arquivo:scripts/llm_router.py] Ponto de roteamento referenciado existe.
- [comando:python -c "import ast; ast.parse(open('scripts/llm_router.py',encoding='utf-8').read())"] Roteador continua com sintaxe válida.
- Critério manual: tarefa com spans mostra caminho crítico com tempos por etapa.
- Critério manual: sem chave externa tudo funciona só local sem aviso repetido.
- Critério manual: nenhuma mudança visual ou de interface acompanha a entrega.

## Definition of Done

- [ ] Cliente implementado em `scripts/eco_trace.py` conforme os requisitos.
- [ ] Pontos iniciais ligados em roteador, ferramentas, agenda e sandbox.
- [ ] Exportador opcional com falha suave e fila local demonstrados.
- [ ] Evidências: resumo com gargalo real extraído de trace verdadeiro.
- [ ] Código versionado no git via gate (`persistencia.ps1`).

## Riscos

- Overhead alto em caminho quente — severidade média (mitigado por amostragem e lote assíncrono).
- Vazamento de segredo em atributo — severidade alta (mitigado por redação antes de gravar).
- Disco cheio com traces — severidade baixa (mitigado por rotação com teto e descarte antigo).
- Backend lento travando tarefa — severidade média (mitigado por fila local com envio fora do caminho).
- Complexidade antes da escala — severidade média (mitigado por API mínima com três funções).

## Testes Relacionados

- scripts/llm_router.py
- scripts/tool_orchestrator.py
- scripts/eco_agenda.py
