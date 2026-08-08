---
tipo: padrao
tags: [android, soundpool, som-personalizado, supermercado-caixa, audio]
data: 2026-08-08
contexto: Supermercado Caixa — adicionar 6 efeitos sonoros e som personalizado ao botão Adicionar
decisao: SoundPool com 9 efeitos pré-carregados + opção de som custom via ACTION_OPEN_DOCUMENT
impacto: v1.5.0 (versionCode 6) — seleção persistente, cancelamento seguro, sem crash
---

# Sons personalizados no Supermercado Caixa (v1.5.0)

## O que foi feito
- 6 novos efeitos sonoros WAV em `res/raw/`: moeda, barcode, sucesso, erro, clique, gaveta (somando aos 3 existentes: caixa, pop, bip).
- Constantes `SOUND_*` e `KEY_CUSTOM_SOUND_PATH`; `playAddSound()` usa switch por constante.
- Opção "Meu próprio som..." abre `ACTION_OPEN_DOCUMENT` (audio/*), copia o arquivo para `getFilesDir()` interno e persiste o caminho absoluto.
- RadioGroup na Config com 10 opções.

## Bugs encontrados e corrigidos
1. **Cancelar o seletor deixava o app travado em custom sem arquivo.** Fix: campo `previousSound`; no cancelamento (`onActivityResult`) reverte `currentSound`, salva e re-checa o rádio correto.
2. **Boot com SOUND_CUSTOM salvo sem arquivo.** Fix: guarda no `onCreate` — se `currentSound == SOUND_CUSTOM && soundCustomId == -1`, reverte para o padrão.
3. **ResetAllData** agora desfaz o som custom (unload + path null + re-check).

## Aprendizado técnico
- `aapt` empacota automaticamente tudo em `res/raw/`; referenciar como `R.raw.nome`.
- Nunca guardar a content Uri; copiar para storage interno e guardar o caminho.
- Extensão original via `OpenableColumns.DISPLAY_NAME` (Cursor no content resolver).
- `adb install -r` preserva dados (update); versionCode 5→6 / 1.4.0→1.5.0.

## Pendência de validação manual
- Seleção real de arquivo no seletor de arquivos do MIUI não pôde ser validada via uiautomator (navegação instável). Lógica de cópia compilada e padrão; validar manualmente no dispositivo.
