---
descricao: Camada de especificacoes (specs) do ecossistema — formato versionado de spec-driven development (SDD)
status: ativa
versao: 1.0.0
data: 2026-08-13
---

# Specs — Camada de Especificações do Ecossistema

Esta pasta contém as especificações versionadas de comportamentos, scripts,
serviços e módulos do EcoSystemUmGrau. Cada spec é um contrato executável:
descreve o que o código deve fazer e o validador (`scripts/valida_specs.py`)
confere se o código realmente implementa o que a spec promete.

## Por que specs versionadas

A Constituição já impõe o comportamento spec-driven (meta-regras do Protocolo de
Engenharia: requisito, critérios de aceitação, definition of done, evidência).
Este diretório fecha a lacuna mecânica: o artefato físico, versionado no git,
que materializa o contrato entre "o que foi pedido" e "o que foi entregue".

Benefícios:

- Contrato explícito e rastreável para cada componente.
- Validação automática via `valida_specs.py` (código referenciado existe, testes existem).
- Fonte única para a geração de specs pelo LER (GoalAnalyzer) e pela compreensão
  de pedidos (`criterios_sucesso`).

## Formato de arquivo

Toda spec é um arquivo Markdown com frontmatter YAML e seções obrigatórias.
O nome segue o padrão kebab-case: `specs/<componente>.spec.md`.

```text
specs/
├── README.md          # este arquivo
├── template.md        # modelo para criar novas specs
└── <componente>.spec.md
```

### Frontmatter (metadados obrigatórios)

| Campo     | Obrigatório | Descrição                                    |
|-----------|-------------|----------------------------------------------|
| id        | sim         | Identificador único (ex: `spec-vigilante-quiet-period`) |
| versao    | sim         | Versão semântica da spec (ex: `1.0.0`)       |
| status    | sim         | `proposta`, `ativa`, `deprecada`             |
| componente| sim         | Caminho do código alvo (ex: `scripts/vigilante.ps1`) |
| tags      | não         | Lista de tags para busca semântica           |
| data      | sim         | Data de criação (AAAA-MM-DD)                 |

### Seções obrigatórias

1. `## Objetivo` — frase única do comportamento especificado.
2. `## Requisitos` — lista numerada dos requisitos funcionais.
3. `## Restrições` — lista de restrições (ambiente, linguagem, estilo, limites).
4. `## Dependências` — lista de dependências (arquivos, módulos, serviços).
5. `## Premissas` — lista de premissas assumidas.
6. `## Entradas e Saídas` — contratos de entrada/saída observáveis.
7. `## Casos de Borda` — comportamentos em condições-limite.
8. `## Critérios de Aceitação` — critérios verificáveis (contrato de validação).
9. `## Definition of Done` — lista de DoD.
10. `## Riscos` — lista de riscos com severidade.
11. `## Testes Relacionados` — caminho(s) do(s) teste(s) que cobrem a spec.

Os campos `## Critérios de Aceitação` e `## Definition of Done` são o contrato
usado por `scripts/valida_specs.py`. Cada critério deve ser verificável
automaticamente (existência de arquivo, execução de comando, teste que passa).

## Como validar

```powershell
python scripts/valida_specs.py              # valida todas as specs
python scripts/valida_specs.py --spec specs/vigilante-quiet-period.spec.md
python scripts/valida_specs.py --json       # saída em JSON (para automação)
```

O validador:

- Parseia frontmatter e seções de cada `.spec.md`.
- Confere que o `componente` referenciado existe no disco.
- Confere que cada arquivo listado em `Testes Relacionados` existe.
- Verifica critérios de aceitação declarados como arquivos/comandos existentes.
- Emite relatório (texto ou JSON) e exit code 0 (ok) / 1 (falhas).

## Ciclo de vida

1. `proposta` — spec criada antes da implementação (TDD/SDD).
2. `ativa` — spec validada e código implementado conforme o contrato.
3. `deprecada` — componente removido ou comportamento substituído; a spec fica
   para histórico e é excluída da validação.

## Integração

- **LER** (`ler-runtime/agent/goal_analyzer.py`): `GoalSpecification` gera o
  conteúdo das seções (objective, requirements, constraints, dependencies,
  assumptions, acceptance_criteria, definition_of_done, risks). A spec markdown
  é o artefato persistente da análise.
- **Compreensão de pedidos** (`mcp/nucleo/habilidades/compreensao-pedidos/`):
  `criterios_sucesso` do entendimento alimenta os `## Critérios de Aceitação`
  da spec versionada.
- **Vigilante**: o FileSystemWatcher observa `specs/` como qualquer outra pasta
  de aprendizado; mudanças em specs geram validação e commits via gate.
