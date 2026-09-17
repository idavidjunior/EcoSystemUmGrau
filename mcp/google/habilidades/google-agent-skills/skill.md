---
name: google-agent-skills
description: |
  Padrão aberto de skills de agentes do Google (Agent Skills): estrutura, criação, boas práticas e integração.
  Trigger phrases: "Google Agent Skills", "agent skills", "criar skill", "SKILL.md", "skill de agente", "skill do google"
allowed-tools: Read, Grep, Write, Edit, Bash, WebFetch
version: 1.0.0
---

# Google Agent Skills

## O que é

O Google Agent Skills é um padrão aberto para empacotar conhecimento de agentes de IA em skills reutilizáveis. Cada skill é uma pasta com um arquivo SKILL.md contendo instruções que o agente segue quando a tarefa combina com a skill.

## Estrutura de uma skill

Uma skill é uma pasta com, no mínimo, um arquivo SKILL.md:

- SKILL.md: obrigatório, contém metadados e instruções
- scripts/: opcional, código executável
- references/: opcional, documentação de apoio
- assets/: opcional, modelos e recursos

## Formato do SKILL.md

O arquivo SKILL.md usa frontmatter YAML seguido de conteúdo Markdown:

```markdown
---
name: nome-da-skill
description: Descrição do que a skill faz e quando usar.
---

# Instruções da skill
...
```

Campos do frontmatter:

- name: obrigatório, até 64 caracteres, minúsculas, números e hífens. Deve casar com o nome da pasta.
- description: obrigatória, até 1024 caracteres. Precisa dizer o que a skill faz e quando usar.
- license: opcional. Exemplo: Apache-2.0.
- metadata: opcional, mapa de chave e valor.
- compatibility: opcional, pré-requisitos de ambiente.
- allowed-tools: opcional, ferramentas pré-aprovadas.

## Como o agente usa skills

O agente segue o padrão de revelação progressiva:

1. Descoberta: no início da conversa, vê a lista de skills com nome e descrição.
2. Ativação: se a descrição combina com a tarefa, lê o conteúdo completo do SKILL.md.
3. Execução: segue as instruções da skill durante a tarefa.

## Boas práticas

- Uma skill por responsabilidade. Skills focadas são melhores que uma skill "faz tudo".
- Descrição específica: diga o que faz e quando é útil. É isso que o agente usa para decidir ativar.
- Scripts como caixa-preta: use-os para operações; não force o agente a depurar o interior.
- Arquivos de referência pequenos e focados. O agente carrega só o que precisa.
- Aproveitar a revelação progressiva: deixe no SKILL.md só o essencial; detalhamento vai para references/.

## Diferença em relação às skills locais

As skills deste ecossistema vivem em mcp/<dominio>/habilidades/<nome>/skill.md. As skills do Google seguem o mesmo conceito, mas usam SKILL.md (maiúsculo) e pastas auxiliares (scripts, references, assets). Este local serve como ponto de estudo e conversão entre padrões.

## Referências úteis

- Especificação do padrão: agentskills.io/specification
- Repositório google-gemini/gemini-skills (skills oficiais da Google)
- Google Cloud Skill Registry (registro e gerenciamento de skills)

## Saída esperada

- Consulta: explicar o padrão, a estrutura e o formato de uma skill
- Criação: montar a pasta da skill com SKILL.md e recursos conforme a especificação
- Conversão: adaptar skill local para o formato Agent Skills ou vice-versa