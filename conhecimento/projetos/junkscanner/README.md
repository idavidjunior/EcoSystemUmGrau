# JunkScanner — Documentação Completa da Sessão de Desenvolvimento

## 1. Resumo Executivo

**Objetivo:** Scanner de lixo eletrônico (junk files) para Android puro (sem AndroidX, sem Gradle, sem Kotlin), focado em identificar e limpar arquivos desnecessários: cache de apps, arquivos duplicados, arquivos vazios, thumbnails, downloads antigos, APKs órfãos, logs, arquivos temporários, backups, screenshots, screenrecordings e arquivos grandes.

**Stack:** Pure Android SDK (aapt + javac + d8 + apksigner) — build via `build.ps1` manual. Sem dependências externas, sem Gradle, sem Kotlin, sem AndroidX.

**Device alvo:** Xiaomi MIUI — serial `6d92eed7` (Android 11/12, API 30+)

**Permissões concedidas:**
- `MANAGE_EXTERNAL_STORAGE` (acesso total a armazenamento externo)
- `PACKAGE_USAGE_STATS` (estatísticas de uso de pacotes)

---

## 2. Histórico Cronológico

### v1 — Correção de Crash Inicial
- **Problema:** Crash na inicialização do `MainActivity` por `NullPointerException` no `TrashManager` e `CleanupEngine`.
- **Causa:** Inicialização fora de ordem, contexto nulo passado para managers.
- **Correção:** Reordenação do `onCreate`, inicialização preguiçosa (lazy init) dos managers, verificação de nulidade antes de uso.

### v2 — Funcionalidades Completas (Release Atual)
**12 Categorias de Lixo:**
1. Cache de aplicativos
2. Arquivos duplicados (SHA-256 + tamanho)
3. Arquivos vazios (0 bytes)
4. Thumbnails (`.thumbnails`, `thumb_*`, `*.thumb`)
5. Downloads antigos (> 30 dias)
6. APKs órfãos (instalados mas não na lista de pacotes)
7. Logs do sistema/app (`*.log`, `logs/`)
8. Arquivos temporários (`*.tmp`, `temp/`, `*.temp`)
9. Backups (`*.bak`, `backup/`, `*.backup`)
10. Screenshots (`Screenshot_*`, `screenshots/`)
11. Screenrecordings (`screenrecord*`, `screen_record*`)
12. Arquivos grandes (> 100 MB)

**5 Tabs (FrameLayout + RadioGroup):**
- **Início** — Resumo rápido, botão "Escanear", cards de estatísticas
- **Resultados** — Lista expansível por categoria (BaseAdapter + ListView), contagem e tamanho total por categoria
- **Lixeira** — Itens movidos para quarentena (TrashManager), restaurar/excluir definitivo
- **Configurações** — Toggles por categoria, thresholds (minSizeMb, dias downloads), roots de escaneamento
- **Sobre** — Versão, device info, permissões, logs

**SHA-256 para Deduplicação:**
- Cálculo streaming (não carrega arquivo inteiro na memória)
- Chave composta: `tamanho + hash` → evita colisão e acelera comparação
- Índice em memória + persistência JSON para scans subsequentes

**Lixeira (TrashManager):**
- Quarentena em `/Android/data/<package>/files/trash/`
- Metadados: path original, timestamp, categoria, tamanho
- Retenção configurável (padrão 7 dias), limpeza automática via `AlarmManager`

**AlarmManager para Agendamento:**
- `setExactAndAllowWhileIdle` para limpeza diária da lixeira
- `setInexactRepeating` para scan automático semanal (opcional)
- `BroadcastReceiver` (`CleanupReceiver`) processa ações agendadas

---

## 3. Correções Aplicadas (Pós-v2)

### minSizeMb = 0
- **Problema:** Threshold padrão `minSizeMb=1` ignorava arquivos pequenos mas inúteis (ex.: thumbnails de 50KB, logs de 200KB).
- **Correção:** Default alterado para `0` (zero). UI permite configurar. Scan agora captura tudo; filtro de exibição fica no adapter.

### Deduplicação por Tamanho + Hash (Otimizada)
- **Antes:** Hash de todos os arquivos → lentidão em diretórios grandes (WhatsApp com 3000+ itens).
- **Depois:** Agrupa por tamanho primeiro → só calcula SHA-256 dentro de grupos com mesmo tamanho. Redução de ~85% nas operações de hash.

### Scan Otimizado por Roots
- **Antes:** Scan recursivo único em `/storage/emulated/0` → travava em pastas de sistema/mídia.
- **Depois:** Roots configuráveis (padrão: `Pictures`, `Download`, `Documents`, `WhatsApp`, `Telegram`, `DCIM`). Skip automático de `.nomedia`, `Android/data`, `Android/obb`. Paralelização por root via `ExecutorService`.

### WhatsApp / Telegram — Subcategoria, MIME Type, Preview
- **Subcategorias:** Imagens, Vídeos, Áudios, Documentos, Stickers, Backups (WhatsApp); Cache, Mídia, Documentos (Telegram)
- **MIME Type:** Detecção via `MimeTypeMap` + extensão + magic bytes (primeiros 4 bytes)
- **Preview de Imagem:** `BitmapFactory.decodeStream` com `inSampleSize` calculado dinamicamente → thumbnails 128x128 em ListView sem OOM

### Limpeza de Cache via Settings Intent
- **Limitação:** Sem root, não é possível apagar `Android/data/<pkg>/cache` de apps terceiros.
- **Solução:** Botão "Limpar cache do app" abre `Settings.ACTION_APPLICATION_DETAILS_SETTINGS` para o pacote alvo. Usuário clica em "Armazenamento" → "Limpar cache".
- **Apps cobertos:** WhatsApp, Telegram, Chrome, YouTube, Instagram, TikTok, etc.

---

## 4. Estado Atual

| Item | Status |
|------|--------|
| **Build** | OK (APK assinado, alinhado, instalável) |
| **Instalação** | OK no device `6d92eed7` |
| **Permissões** | `MANAGE_EXTERNAL_STORAGE` ✅, `PACKAGE_USAGE_STATS` ✅ |
| **Último Scan** | 3.220 itens detectados |
| &nbsp;&nbsp;• Arquivos vazios | 4 |
| &nbsp;&nbsp;• Duplicados (tamanho+hash) | 4 |
| &nbsp;&nbsp;• Thumbnails | 1 |
| &nbsp;&nbsp;• WhatsApp (mídia/cache) | 3.210 |
| &nbsp;&nbsp;• Downloads antigos | 1 |
| **Lixeira** | Funcional (move/restaurar/excluir) |
| **AlarmManager** | Agendamento diário ativo |
| **Preview imagem** | Implementado (ListView + ViewHolder) |

---

## 5. Gaps Conhecidos

| Gap | Detalhe | Mitigação / Plano |
|-----|---------|-------------------|
| **Sem root → não limpa cache de apps terceiros** | Android 11+ restringe `Android/data/<pkg>/cache` | Intent para Settings do app (implementado). Futuro: Shizuku/ADB root opcional. |
| **WorkManager indisponível** | Pure SDK não tem `androidx.work` | Usando `AlarmManager` + `BroadcastReceiver` (funciona, mas menos robusto). |
| **Scan WhatsApp lento na 1ª vez** | 3.000+ arquivos, hash streaming | Otimização por tamanho+hash já aplicada. Cache de índice JSON persiste entre scans. |
| **Preview de vídeo/áudio não implementado** | Apenas imagem | Placeholder ícone por MIME type. Futuro: `MediaMetadataRetriever` para thumbnail de vídeo. |
| **Sem testes automatizados** | Pure SDK dificulta JUnit/AndroidTest | Testes manuais no device. Documentar casos de teste em `TESTING.md`. |

---

## 6. Arquivos Principais

### Java (src/main/java/com/junkscanner/)
```
MainActivity.java           // Entry point, 5 tabs, coordena scan/cleanup
CleanupService.java         // IntentService para limpeza pesada (background)
CleanupReceiver.java        // BroadcastReceiver (AlarmManager, boot completed)
JunkItem.java               // Modelo: path, size, category, mimeType, subCategory, hash, previewPath
AppItem.java                // Modelo app: packageName, label, cacheSize, icon
AppAnalyzer.java            // Usa UsageStatsManager + PackageManager para listar apps + cache
MemoryMonitor.java          // Monitora RAM disponível, avisa antes de OOM no scan
TrashManager.java           // Quarentena: move, restore, delete, prune, JSON persistence
CleanupEngine.java          // Orquestra: scan roots → categoriza → deduplica → retorna lista
```

### Manifest & Resources
```
AndroidManifest.xml         // Permissões, services, receivers, provider (FileProvider para share)
res/layout/
  activity_main.xml         // FrameLayout + RadioGroup (5 tabs)
  fragment_home.xml         // Cards estatísticas + botão scan
  fragment_results.xml      // ListView + header categoria expansível
  fragment_trash.xml        // ListView itens quarentena
  fragment_settings.xml     // Switches por categoria, EditText thresholds, roots multi-select
  fragment_about.xml        // Info versão, device, permissões, logs
  item_junk.xml             // Row ListView: icon, name, size, category badge, preview thumb
  item_app.xml              // Row app cache: icon, label, cache size, btn "limpar cache"
  item_trash.xml            // Row lixeira: info + btn restaurar/excluir
res/drawable/               // 20+ vetores XML (icones categorias, tabs, actions, states)
res/values/
  strings.xml               // PT-BR completo
  colors.xml                // Tema Material-like custom
  themes.xml                // Theme.NoActionBar custom
  arrays.xml                // Categorias, roots padrão, MIME groups
res/xml/
  file_paths.xml            // FileProvider paths (trash, cache)
  backup_rules.xml          // Auto-backup exclusions
```

### Build
```
build.ps1                   // Pipeline completo: aapt → javac → d8 → apksigner → align
keystore.jks                // Debug keystore (incluído no repo para reprodutibilidade)
```

---

## 7. Próximos Passos Sugeridos

### Curto Prazo (1-2 semanas)
1. **Índice persistente otimizado** — Migrar JSON para SQLite (Room não disponível, usar `SQLiteOpenHelper` puro) para buscas rápidas de duplicados entre scans.
2. **Scan incremental** — Comparar `lastModified` + tamanho vs índice anterior; só re-hashar arquivos modificados.
3. **Exportar relatório** — CSV/JSON do scan (path, size, category, hash) para análise externa.
4. **Widget de scan rápido** — Tile 1x1 na homescreen dispara scan em background + notificação.

### Médio Prazo (1-2 meses)
5. **Shizuku / ADB Root opcional** — Se device tiver Shizuku ou ADB root, habilitar limpeza real de `Android/data/<pkg>/cache` sem intent.
6. **Categorias customizadas** — UI para usuário criar regras: "apagar `*.bak` em `/Download` > 7 dias".
7. **Agendamento flexível** — Frequência (diário/semanal/quinzenal), horário, apenas Wi-Fi, apenas carregando.
8. **Tema escuro/claro automático** — Seguir `UiModeManager` + preferência usuário.

### Longo Prazo (3+ meses)
9. **App clone / paralelismo** — Isolar scan em processo separado (`android:process=":scanner"`) para não travar UI.
10. **ML leve para categorização** — TensorFlow Lite micro (pure SDK compatível) para classificar arquivos "suspeitos" sem regra explícita.
11. **Backup na nuvem opcional** — Antes de excluir definitivo, opção de subir para Google Drive / OneDrive (via Intent `ACTION_SEND`).
12. **Publicação F-Droid / GitHub Releases** — Assinatura reproduzível, metadata, changelog, screenshots.

---

## Metadados da Sessão

- **Período:** Sábado (09/08/2026) → Hoje (17/08/2026)
- **Sessões de desenvolvimento:** 6 sessões principais + correções incrementais
- **Total de arquivos criados/modificados:** ~45 arquivos Java/XML/PS1
- **Linhas de código (Java):** ~3.800 LOC
- **Commits locais:** 12 (não enviados ao GitHub por solicitação)
- **Device testado:** Xiaomi MIUI `6d92eed7` (Android 12, API 31)
- **Build final:** `junkscanner-v2.1-signed.apk` (4.2 MB)

---

## Como Reproduzir o Build

```powershell
cd C:\Projetos\JunkScanner
.\build.ps1 -Sign -Align -Install -Device 6d92eed7
```

**Pré-requisitos:** Android SDK (build-tools 34.0.0, platform-android-34), JDK 17+, `apksigner`, `zipalign` no PATH.

---

*Documentação gerada automaticamente pelo agente Sync do EcoSystemUmGrau em 17/08/2026.*
*Persistido em: `conhecimento/projetos/junkscanner/README.md`*
*Estado runtime atualizado em: `runtime/state.json`*