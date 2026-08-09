---
tags: [arquivos, backups, decisao, opencode, runner, temporarios]
aliases: [protocolo higiene repo streamumgrau]
date: 2026-08-09
---

# protocolo higiene repo streamumgrau

**Fonte:** opencode

---
tipo: decisao
tags: [github, streamumgrau, organizacao, higiene, build]
data: 2026-08-08
contexto: Continuacao do fluxo de build do StreamUmGrau via GitHub Actions (Flutter compila no runner). Usuario definiu regras de organizacao do repositorio.
decisao: Manter o repo github.com/idavidjunior/stream-um-grau LIMPO. Protocolo fixado:
  1. APK nunca vai para o git - compila no Actions e baixa como artifact.
  2. Nada de lixo: screenshots de debug, logs, builds intermediarios, node_modules, backups, arquivos temporarios.
  3. Commits pequenos, focados e significativos (convencional).
  4. Toda subida requer autorizacao previa do usuario.
  5. Sem abuso de subidas - apenas mudancas reais e revisadas.
impacto: Repositorio enxuto, historico legivel, build reproduzivel via workflow build-apk.yml.
pendente: Nenhuma.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]