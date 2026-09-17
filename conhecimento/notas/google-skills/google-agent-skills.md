---
tags: [google-skills, agent-skills, padrao]
aliases: [Agent Skills, Google Agent Skills, Padrão Agent Skills]
date: 2026-09-15
categoria: google-skills
---

# google-agent-skills — Skills de Agentes do Google

**Categoria:** google-skills
**Fonte:** mcp/google/habilidades/google-agent-skills/skill.md

## Papel

Ponto de entrada do padrão Agent Skills do Google: skills em formato `SKILL.md` com frontmatter `name` e `description`, vendidas em pacotes localizados na pasta `skills/`. A `description` é analisada pelo tempo de execução para decidir quando carregar a skill. Uso: `python -m auth_skill` via Gemini CLI.

## Estrutura de uma skill

- `SKILL.md` — o corpo principal, com frontmatter (name, description) e corpo em Markdown
- `references/` — documentação detalhada opcional (Deep Dives), sem limite à revelação progressiva
- `scripts/` — utilitários executáveis chamados pela skill
- `LICENSE` — licença obrigatória em cada skill (geralmente Apache 2.0)

## Boas práticas do padrão

- Primeira linha da descrição: ação (verb) + resultado (noun) + contexto
- Frontmatter é minúsculo (`name`, `description`), separados por duas novas linhas do corpo
- Corpo estruturado: Overview de contexto, o que procurar/quando usar, exemplo de entrada → saída, parâmetros e passos, checklist final
- Revelação progressiva: `SKILL.md` contém apenas o essencial; referências/resumo em diretório `references/`

## Conexões

- [[cluster-hub-google-skills]] — hub do cluster das skills do Google
- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[gemini-api-dev]] — skill oficial: SDK, modelos e Interações (Interactions API)
- [[gemini-live-api-dev]] — skill oficial: streaming em tempo real via WebSocket
- [[gemini-omni-flash-api]] — skill oficial: geração e edição de vídeo generativo