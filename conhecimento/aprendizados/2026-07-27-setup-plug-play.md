# 2026-07-27 - Setup Plug & Play e organizacao GitHub

## O que foi feito
- Repositorios do GitHub mapeados: 11 existentes, nenhum LER separado
- setup.bat criado: script unico para qualquer PC novo (clona, instala, configura, pede API keys)
- config/opencode.jsonc: template com {{USERPROFILE}} placeholder para geracao dinamica
- config/agents/: fonte unica dos 15 agentes OpenCode (repo eh source of truth)
- config/opencode-model-fallback.jsonc: config do plugin fallback
- Vigilante atualizado: sincroniza EcoSystemUmGrau (com push) e LER local (sem remote)
- LER remote removido do GitHub e localmente (conhecimento viaja no EcoSystemUmGrau)

## Decisao
- Nao criar repos separados para ferramentas do ecossistema (LER)
- Toda config e agente vive no repo EcoSystemUmGrau/config/
- setup.bat gera os arquivos no destino a partir dos templates (nada duplicado)
- gh CLI instalado (nao autenticado, token sem escopo read:org)

## Padrao
- setup.bat na raiz do repo para bootstrap em maquina nova
- Templates com {{VAR}} substituidos por script de setup
- Repo unico = fonte unica de verdade
