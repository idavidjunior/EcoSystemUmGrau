# Multimídia — Habilidades de áudio, imagem e vídeo

> Catálogo único: `Habilidades/` · Categoria: `multimidia`

## Propósito

Reúne habilidades **executáveis** que produzem, transformam ou interpretam conteúdo
multimídia (áudio, imagem, vídeo) — geração, edição, transcrição, metadados, OCR, etc.

## Critérios de admissão

Uma habilidade entra em `multimidia/` quando a **entrada e/ou saída principal é conteúdo
multimídia**. Habilidades que apenas *manipulam arquivos* sem tratar o conteúdo (ex.:
resgatar metadados de MP3) podem pertencer a `tecnicas/`, a critério da revisão do
manifesto.

## Decisão da revisão do manifesto (2026-07-31)

- `mp3player-metadata-rescue` **permanece em `tecnicas/`**: a habilidade é rescate de
  metadados (manipulação técnica de tags/estrutura de arquivo), não produção/edição de
  mídia. Categorização mantida — ver `manifesto_geral.json`.

## Habilidades previstas

Nenhuma habilidade multimídia foi catalogada ainda. Candidatas futuras:

- transcrição de áudio (STT) e síntese de fala (TTS) — hoje parte da infra do Jarvis
  (`edge-tts`/SpeechRecognizer no app Android), não uma habilidade isolada;
- geração de imagem (provider `nvidia`/`qwen-image`) — hoje usada pontualmente no Jarvis;
- OCR de imagens/PDFs.

Quando uma delas virar habilidade executável autônoma, criar a subpasta em `multimidia/`
e registrar no `manifesto_geral.json` com `"categoria": "multimidia"`.
