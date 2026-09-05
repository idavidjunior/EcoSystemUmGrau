---
tags: [erros, exception, imagem, opencode, padrao, rede]
aliases: [Regra do usuário: build/instala/testa/valida antes de commit]
date: 2026-08-08
---

# Regra do usuário: build/instala/testa/valida antes de commitar e subir

**Fonte:** opencode

## A regra (declarada pelo usuário)

> "Antes de commitar deve ser compilado, instalado, testado e validado. Só depois subir para o GitHub."

## Ciclo obrigatório (ordem fixa)

1. **Compilar** — `flutter build apk --debug` (build local, via Flutter 3.44.9 em `.flutter_auto/flutter`)
2. **Instalar** — `adb -s 100.64.71.9:5555 install -r -t build/app/outputs/flutter-apk/app-debug.apk`
3. **Testar** — `flutter analyze` (sem issues) + `flutter test` (passando) + iniciar o app no Redmi
4. **Validar** — app abre sem crash (`Displayed`/`Fully drawn` no logcat, PID vivo, sem `FATAL EXCEPTION`, sem erros de rede/imagem do app)

Só então: **commit + push**.

## Detecção de falha de processo (corrigida na mesma sessão)

- O push `2643d6b` (mock corrigido 8/8 + script TMDB + guia) foi feito ANTES da validação local completa.
- Correção: o build local (66s) + instalação (`Success`) + validação (PID 12396, `Displayed` em 5s845ms, sem FATAL) foram executados logo após o push.
- O CI enxuto do repo (p
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]