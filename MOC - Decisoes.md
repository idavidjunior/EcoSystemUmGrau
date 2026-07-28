# Mapa de Conteúdo — Decisões

## Arquiteturais

| Decisão | Fonte | Data |
|---------|-------|------|
| LER usa Python puro (stdlib only) — zero dependências | ler_arquitetura | — |
| Estado persiste em JSON (human-readable, sem migrations) | ler_arquitetura | — |
| Checkpoints salvos antes de cada iteração | ler_arquitetura | — |
| Pontuação ponderada com 6 categorias | ler_arquitetura | — |
| Estratégia selecionada por ranking (cost+risk+time+complexity+success) | ler_arquitetura | — |
| Supervisor monitora módulos individualmente | ler_arquitetura | — |
| Metadata multi-fontes: AcoustID → iTunes BR → MusicBrainz → iTunes US | mp3player | — |
| SearchMode.NORMAL → RELAXED auto-fallback | mp3player | — |
| Album art com redirect loop manual | mp3player | — |
| Single Activity + FrameLayout (sem Fragments) | android_pure_sdk | — |
| Form Starts Empty | android_pure_sdk | — |
| Salvar cria novo arquivo timestampado | android_pure_sdk | — |
| TextView > Button para botões customizados | mp3player_android | 2026-07-28 |

## Infraestrutura

| Decisão | Fonte | Data |
|---------|-------|------|
| Chaves API exclusivamente em env vars | sessao_seguranca | — |
| Server health check via HTTP ping | sessao_servermanager | — |
| Salvar RustDesk password fixo (não OTP) | sessao_rustdesk | — |
| Priorizar data-testid sobre classes CSS | treinamento_navegacao | — |
| Mudar config MCP de objeto para array | provider_mcp_debug | — |
| Abastecer estruturas existentes (7 categorias) | ecosistema_regra_ouro | — |
| Organizar Desktop\Codigos\ como raiz única | workspace_organization | — |
| Renomear pastas com espaços | workspace_organization | — |

## Aprendizados do Ecossistema

\`\`\`dataview
TABLE file.cday as "Data"
FROM "conhecimento/aprendizados"
WHERE contains(file.name, "decisao") OR contains(file.name, "setup") OR contains(file.name, "unificacao") OR contains(file.name, "correcao")
SORT file.cday DESC
\`\`\`

> **Fonte completa:** [[ler-runtime/CONHECIMENTO.md]]
