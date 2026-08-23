---
tipo: padrao
tags: [cli-anything, soberania, internalizacao, opencode, habilidades]
data: 2026-08-22
contexto: Instalação do projeto externo HKUDS/CLI-Anything no ecossistema, com diretriz do usuário de que toda capacidade externa deve ser assimilada e internalizada para garantir autossuficiência.
---

# CLI-Anything Internalizado como Habilidade Soberana

## Decisão
Instalar os 5 comandos globais do CLI-Anything em ~/.config/opencode/commands/ e simultaneamente destilar a metodologia HARNESS.md (37 KB, 7 fases) numa habilidade própria do ecossistema: mcp/desenvolvimento/habilidades/cli-anything/skill.md, com o documento completo preservado em references/HARNESS.md dentro da própria pasta.

## Impacto
O ecossistema ganha a capacidade de transformar qualquer software de código aberto numa CLI controlável por agentes. A versão interna é carregada globalmente via instructions (mcp/**/habilidades/**/skill.md) e sobrevive à descontinuação ou perda do projeto externo. Padrão a replicar em futuras instalações de capacidades externas: instalar + internalizar + registrar.

## Fonte original
HKUDS/CLI-Anything (MIT), metodologia GUI-to-CLI em 7 fases: análise do codebase, arquitetura CLI, implementação, plano de testes prévio, testes com software real, documentação dos resultados, geração de skill e refinamento iterativo.

## Conexoes

- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]