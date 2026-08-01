# electron-app-gpu-disable-flags

**Categoria:** padrão técnico
**Problema:** App Electron/Chromium fecha ou fica com janela branca em GPU antiga (driver de anos atrás, ex.: Intel HD 4xxx/5xxx com driver de 2015).
**Quando aplicar:** qualquer app Electron que crasha o renderer/GPU em hardware legado; diagnóstico antes de desistir do app.

## Flags de linha de comando (ordem canônica)

```
--disable-gpu --disable-gpu-compositing --in-process-gpu --no-sandbox
```

| Flag | O que faz |
|---|---|
| `--disable-gpu` | Desliga aceleração por hardware (software rendering). Resolve o crash do processo GPU. |
| `--disable-gpu-compositing` | Desliga a composição por GPU (evitaasso de UI em buffers GPU). |
| `--in-process-gpu` | Roda o GPU no processo principal em vez de processo filho (evita crash isolado que derruba o renderer). |
| `--no-sandbox` | Desliga o sandbox do Chromium. Necessário porque `--in-process-gpu` é incompatível com sandbox. **Reduz segurança** — só usar em desktop local confiável. |

## Onde aplicar

- **Atalhos `.lnk`** (Desktop + Start Menu) via `WScript.Shell.CreateShortcut().Arguments` — sobrevive a updates do app.
- Não há config de settings.json do Electron que desligue GPU de forma universal; a flag de linha de comando é o padrão.

## Ordem de teste (do menor ao maior impacto)

1. `--disable-gpu` só (costuma bastar para crash de GPU).
2. `+ --disable-gpu-compositing` (se ainda houver artefato UI).
3. `+ --in-process-gpu` (se ainda houver derrubada de renderer).
4. `+ --no-sandbox` (último recurso, exige `--in-process-gpu`).

## Verificação pós-aplicação

- Ausência de `utility.log` com `child process gone { type: 'GPU' }` = GPU não crashou.
- Ausência de `window.log` com `app render process gone { reason: 'crashed' }` = renderer não crashou.
- `renderer.log` crescendo (app ativo) + janela `Responding=True` + captura com conteúdo (centenas de cores) = UI renderizada.

## Armadilhas

- App fecha **sem** logs de crash → não é GPU; é pressão de memória (Windows OOM). Veja `prepend-tool/memory-pagefile` antes das flags.
- Atualizações do app podem **recriar** atalhos sem as flags — revalidar após update.
- `--no-sandbox` só em máquina local confiável; nunca em conteúdo não confiável / navegação web.
