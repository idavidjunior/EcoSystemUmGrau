---
tipo: erro
tags: [preflight, etica, terceiros, scanner, falso-bloqueio]
data: 2026-09-08
contexto: Commit de validação da busca web foi bloqueado pelo Preflight Ético com 4 bloqueios "segredo hardcoded" apontando para READMEs do OpenManus (projeto de terceiros não rastreado no git, com placeholders sk-.../bu_... de exemplo).
decisao: Adicionar 'OpenManus' aos diretórios ignorados do scanner ético (skip_dirs em preflight_etica.py), mesma política já aplicada a node_modules, vendor, dist e build.
impacto: Preflight Ético voltou a nível medio APROVADO com 28 WARNs aceitos (sem bloqueio). Repos de terceiros clonados na raiz não devem ser varridos como código do ecossistema.
---

# Ajuste: scanner ético ignora OpenManus (terceiros)

## Sintoma
- `persistencia.ps1 commit -Push` falhou em PREFLIGHT_FAIL.
- Preflight check: [7] Preflight Etico -> BLOQUEADO: 4 bloqueio(s) ético(s).
- Os 4 bloqueios: `OpenManus\README.md`, `README_ja.md`, `README_ko.md`, `README_zh.md` — "segredo hardcoded".

## Causa raiz
- `scan_repo()` de `scripts/preflight_etica.py` varre o working tree inteiro via `os.walk(BASE)`, saltando apenas os dirs de `skip_dirs`.
- O nível ético "medio" bloqueia `segredos_crus` (mapa `segredo hardcoded` -> chave `segredos_crus` em `_promover_warns_por_nivel`).
- OpenManus é um repo de terceiros (clonado na raiz, não rastreado — status `??`), cujos READMEs contêm exemplos de API key com placeholder (`sk-...`, `bu_..."`) — não são credenciais reais, mas o regex `\b(api[_-]?key|secret|token)\b ... = "..."` casava.

## Corrigido
- Adicionado `'OpenManus'` aos `skip_dirs` em `scan_repo()` e ao set `skip` em `data_inventory()` (scripts/preflight_etica.py).
- Coerente com a política de "Pastas ignoradas: terceiros, cache, backups e estados efemeros".

## Evidência
- `python scripts/preflight_etica.py` (background, log etico4.log): `APROVADO com 28 alerta(s) de revisao.` — volta ao baseline de 28 WARNs (sem bloqueio).

## Aprendizado
- Repos de terceiros clonados na raiz do workspace são varridos pelo scanner ético e podem gerar falso bloqueio (placeholders de exemplo). Manter na lista de ignorados.
- Preflight check demora ~240s (chama o preflight ético interno com timeout de 240s na linha 411); rodar em background com redirect.
- Processos duplicados de preflight_check podem surgir se o shell matar o processo pai do Start-Process (ChildProcess.kill) sem matar o filho; conferir e encerrar órfãos antes de revalidar.
