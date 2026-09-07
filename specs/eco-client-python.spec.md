---
id: spec-eco-client-python
versao: 0.1.0
status: ativa
componente: scripts/eco_client.py
tags: [runtime, python-client, api-embarcada, stdlib, integracao]
data: 2026-09-07
---

# Spec — Cliente Python Embutido

## Objetivo

O cliente Python embutido expõe o runtime do ecossistema via import direto, sem subprocesso e sem mudar a interface.

## Requisitos

1. O módulo vive em `scripts/eco_client.py` e é importável com `from eco_client import EcoClient` após ajuste de `sys.path`.
2. O cliente reutiliza os módulos existentes via import direto, sem duplicar lógica de estado ou memória.
3. O cliente expõe boot e status via `runtime_boot` e `runtime_state`, com retorno em dicionário.
4. O cliente expõe leitura e escrita de estado, pendências, agentes ativos, checkpoint e histórico via `runtime_state`.
5. O cliente expõe gravação e busca de memória via `memory_engine`, com redação automática de segredos preservada.
6. O cliente expõe carregamento de contexto relevante via `runtime_context`, sem carregar a memória inteira.
7. O cliente expõe validação de saída via `runtime_kernel` e auditoria via `runtime_auditor`, com criticidade configurável.
8. O cliente oferece consulta ao maestro via `maestro_client`, com fallback degradado quando o maestro está offline.
9. O cliente nunca executa git direto, nunca altera a interface e nunca exige dependência além da biblioteca padrão.
10. O cliente acompanha teste de fumaça que importa, instancia, lê status e executa um ciclo de checkpoint em diretório temporário.

## Restrições

- Python 3 puro com apenas biblioteca padrão, sem dependências externas.
- Windows PowerShell 5.1 e caminho com espaços devem funcionar sem ajuste manual.
- Escrita atômica com temporário mais `os.replace`, seguindo o padrão do runtime.
- Falha suave em toda operação opcional, nunca lançando exceção para o chamador em consulta simples.
- Respeito às cláusulas de ponto único de persistência, idioma pt-BR e deveres externos.

## Dependências

- `scripts/runtime_boot.py` — verificação de integridade e restauração de estado.
- `scripts/runtime_state.py` — funções `load_state`, `save_state`, pendências, agentes e checkpoints.
- `scripts/memory_engine.py` — funções `add_memory`, `query`, `get_context` e `stats`.
- `scripts/runtime_context.py` — carregamento seletivo de contexto por assunto.
- `scripts/runtime_kernel.py` — validação de contrato de saída e classificação de complexidade.
- `scripts/runtime_auditor.py` — auditoria adaptativa por criticidade.
- `scripts/maestro_client.py` — consulta ao maestro com protocolo de caixa de correio.

## Premissas

- Python 3 disponível no PATH com codificação UTF-8 no ambiente.
- O repositório do ecossistema é a raiz que contém as pastas `scripts`, `runtime` e `conhecimento`.
- O chamador importa o cliente de dentro do repo ou ajusta o caminho da pasta `scripts`.
- O maestro pode estar offline e o cliente continua operando em modo degradado.

## Entradas e Saídas

- Entrada: objetivo em texto, chave e valor de estado, texto de memória, assunto de contexto e resposta para auditar.
- Saída: dicionários com `ok`, dados e motivo de falha quando aplicável, sem exceção em consultas simples.
- Efeito colateral: atualização de `runtime/state.json`, checkpoints, memórias e log de maestro offline quando acionado.

## Casos de Borda

- Estado ausente na primeira execução: cria estado padrão e retorna vazio sem erro.
- Memória vazia ou corrompida: busca retorna lista vazia e gravação preserva o que é válido.
- Maestro offline: consulta retorna estado offline e registra alerta sem bloquear o chamador.
- Contexto sem assunto: retorna contexto mínimo do projeto ativo em vez de falhar.
- Concorrência entre processos: escrita usa trava e arquivo temporário, sem corrupção parcial.
- Caminho base fora do repo: resolução sobe pelos pais até achar `scripts` e `runtime`.

## Critérios de Aceitação

- [arquivo:scripts/eco_client.py] Componente existe e é o alvo da spec.
- [arquivo:scripts/test_eco_client.py] Teste de fumaça do cliente existe.
- [comando:python scripts/preflight_check.py] Preflight técnico passa sem erros.
- [comando:python scripts/valida_specs.py --spec specs/eco-client-python.spec.md] Validador da spec passa sem erros após a implementação.
- Critério manual: um script externo importa o cliente, lê o status e grava uma memória de teste sem usar subprocesso.
- Critério manual: nenhuma mudança visual ou de interface acompanha a entrega do cliente.

## Definition of Done

- [ ] Cliente implementado em `scripts/eco_client.py` com API conforme a spec.
- [ ] Teste de fumaça criado e aprovado em `scripts/test_eco_client.py`.
- [ ] Preflight técnico e ético executados e aprovados.
- [ ] Evidências: importação direta e ciclo de checkpoint demonstrados em log.
- [ ] Código versionado no git via gate (`persistencia.ps1`).

## Riscos

- Import circular entre cliente e módulos do runtime — severidade média (mitigado por imports tardios e falha suave).
- Uso fora do repo com caminho errado — severidade baixa (mitigado por resolução automática da base).
- Concorrência em escrita de estado — severidade média (mitigado por trava e escrita atômica existentes).
- Exposição de segredo via memória — severidade alta (mitigado por redação automática preservada do motor de memória).

## Testes Relacionados

- scripts/preflight_check.py
- scripts/preflight_etica.py
- scripts/valida_specs.py
