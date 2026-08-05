# Ponytail — Habilidade comportamental "Lazy senior dev"

> Catálogo único: `Habilidades/` · Categoria: `comportamentais` · Entrypoint do manifesto: `manifesto.json`

## Papel no ecossistema

O Ponytail é a **personalidade de trabalho** do ecossistema: o "senior dev preguiçoso" que
mantém a **forma e o estado de trabalho entre sessões**. Ele não executa tarefas — ele
**molda como** o código é escrito e revisado:

- **Simplificar código**: menos camadas, menos abstração, menos cerimônia.
- **Reduzir tokens**: economizar contexto do modelo é prioridade de design.
- **Usar stdlib/ferramentas do ambiente** antes de adicionar dependências.
- **Revisar tudo**: todo código gerado por qualquer agente passa por ele
  (qualidade, simplicidade, redução de tokens) no fluxo natural da sessão.

Linha do tempo no fluxo Maestro: `Ponytail → Todos` (revisão de código entre PLAN e MERGE).

## Como ativa

- **Modo `full`**: ativo quando existe o arquivo `.ponytail-active` (em `~/.config/opencode/`
  ou no diretório de trabalho). Sem ele, atua apenas sob demanda via comandos.
- **Comandos (gatilhos)**:
  - `/preguica` — pede a versão mais simples/preguiçosa possível de uma solução.
  - `/review` — revisa código existente com o olhar de simplicidade/token reduction.
  - `/sarcasmo` — respostas secas e irônicas de senior que já viu tudo.
  - `/clean-code` — aponta e corrige complexidade desnecessária.

## Estrutura alvo

```
Habilidades/comportamentais/ponytail/
├── README.md        # este arquivo — definição da habilidade
├── manifesto.json   # entrypoint no manifesto_geral.json (hooks/gatilhos)
└── comandos/        # cada gatilho (/preguica, /review, /sarcasmo, /clean-code) em um arquivo .md
```

## Estado — origem a localizar

- `plugins/ponytail/` no repo estava **vazio** (por isso foi removido do `plugin` do
  `opencode.jsonc` — Cláusula Pétrea).
- `docs/EcossistemaAgentes.md` e `estado_atual.md` documentam o plugin instalado em
  `~/.config/opencode/plugin/ponytail.mjs`, **mas o arquivo não existe neste PC**
  (migração para máquina nova perdeu o binário; não está no GitHub).
- Enquanto o fonte não for localizado, esta pasta é a **especificação** da habilidade;
  quando o `.mjs` for encontrado, instalar em `~/.config/opencode/plugin/ponytail.mjs`
  **sem** referenciá-lo no JSON (padrão do ecossistema, ver `ler/SKILL.md`) e registrar
  os comandos em `comandos/`.

## Pendências abertas

1. Localizar o `ponytail.mjs` original (ver decisão `2026-07-31-habilidades-catalogo-unico-jarvis`, ponto 3 dos guardrails).
2. Criar `manifesto.json` com hooks/gatilhos quando o fonte for encontrado.
