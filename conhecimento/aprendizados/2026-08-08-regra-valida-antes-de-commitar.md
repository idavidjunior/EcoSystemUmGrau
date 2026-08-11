---
tipo: padrao
tags: [processo, git, validacao, build, streamumgrau, flutter]
data: 2026-08-08
contexto: Fase A do StreamUmGrau - o usuario definiu a ordem obrigatoria do ciclo de desenvolvimento local
decisao: Nenhum commit/push pode ser feito sem antes COMPILAR, INSTALAR, TESTAR e VALIDAR o APK localmente
impacto: Fluxo seguro - codigo que sobe para o GitHub ja foi executado no dispositivo real
---

# Regra do usuário: build/instala/testa/valida antes de commitar e subir

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
- O CI enxuto do repo (pub get → analyze → test → build) atua como rede de segurança, mas a ordem correta é validar LOCAL primeiro.

## Lição

- O CI valida o código, mas NÃO substitui a validação no dispositivo real.
- O fluxo local rápido (build incremental ~66s) permite validar antes de subir sem custo alto.
- O screenshot do app não pôde ser inspecionado visualmente (modelo sem suporte a imagem) — a validação visual dos posters fica com o usuário; a validação técnica (HTTP 200 nas 8 URLs, app sem crash) foi feita por logcat e verificação de URLs.

## Conexoes

- [[cluster-hub-programacao]]
- [[git-fluxos-de-trabalho-trunk-based-e-git-flow-e-quando-usar-]]