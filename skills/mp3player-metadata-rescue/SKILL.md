# Android MP3Player — Metadata Rescue & Build Intelligence

> **IMPORTANT — Auto-Update Rule:** Every time you (the AI) discover a new bug, fix, pattern, architecture decision, or any relevant knowledge about this project, you MUST automatically update this skill file. Do not ask for permission. Do not wait. Just update it. This is how the knowledge base evolves and improves across sessions. New findings go into the "Known Issues & Fixes" table and any relevant section above it. When in doubt, add it — over-documentation is better than lost knowledge.

## Project Overview

- **Package:** `com.mp3player.debug`
- **Platform:** Android 12+ (MIUI 14+), minSdk 26, targetSdk 35
- **Build:** Gradle 8.x + Kotlin + CMake native libraries (fingerprint_jni)
- **Device connection:** ADB over WiFi (`adb connect 100.64.71.9:5555`, also via `adb tcpip 5555`)
- **App name:** "Reprodutor MP3" — Music player with tag editor and metadata online search
- **Repository:** `C:\Users\Playtec-bancada\Desktop\Codigos\Android\Mp3Player`

---

## Build Pipeline

**AUTO-DEPLOY RULE (permanente):** Sempre que fizer qualquer alteracao no codigo, automaticamente:
1. `git add` + `git commit` + `git push origin master`
2. `gradlew assembleDebug`
3. `adb install -r` no dispositivo `100.64.71.9:5555`
Nao esperar confirmacao do usuario para estas etapas.

### Full Debug Build
```powershell
cd C:\Users\Playtec-bancada\Desktop\Codigos\Android\Mp3Player
.\gradlew.bat assembleDebug
```
Output APK: `app/build/outputs/apk/debug/app-debug.apk`

### Install & Run
```powershell
adb -s 100.64.71.9:5555 install -r app/build/outputs/apk/debug/app-debug.apk
adb -s 100.64.71.9:5555 shell am start -n com.mp3player.debug/.MainActivity
```

### Clean Build
```powershell
.\gradlew.bat clean assembleDebug
```

### Build structure
- **Native libs:** CMake (`app/src/main/cpp/`) for `fingerprint_jni` (AcoustID fingerprinting)
- **Kotlin compilation:** KSP for annotation processing (Room, etc.)
- **D8 dexer:** Included auto via AGP (Android Gradle Plugin)
- **APK signing:** Debug keystore auto via AGP (`~/.android/debug.keystore`)
- **No aapt involved** — it's a Gradle project, not pure SDK

### Version Management
`version.properties` in project root — edit manually between builds.

---

## Project Architecture

### Package Structure
```
com.mp3player/
  MainActivity.kt           — Launcher activity (file list)
  TagEditorActivity.kt      — Tag editor with online search
  ui/                       — UI components, adapters, themes
    adapters/
    views/
    theme/
  data/
    model/
      MusicMetadata.kt      — Data class for metadata (title, artist, album, art bytes)
      MusicFolder.kt        — Directory model
    online/
      MetadataSearchService.kt  — Core: multi-source metadata search engine
      AcoustIDService.kt       — Audio fingerprint via AcoustID API
    local/
      MusicDatabase.kt      — Room database
      MusicDao.kt           — Room DAO
  service/
    MusicPlayerService.kt   — Background playback service
  receiver/
    NotificationReceiver.kt — Notification actions
```

### Key Files Reference
| File | Lines | Purpose |
|------|-------|---------|
| `TagEditorActivity.kt` | ~295 | Tag editor UI, triggers search, applies results |
| `MetadataSearchService.kt` | ~510 | Multi-source search engine (iTunes, MusicBrainz, AcoustID) |
| `AcoustIDService.kt` | ~228 | Audio fingerprint generation + AcoustID API |
| `MusicMetadata.kt` | ~20 | Data model with `isComplete` validation |

---

## Metadata Search Pipeline

### Entry Point
`TagEditorActivity.searchOnline()` (line 177) calls `MetadataSearchService.searchAll()`.

### Search Flow (`searchAll()` at line 93)

**Two search modes:**
- `SearchMode.NORMAL` (default) — strict scoring thresholds, tries artist+title+album
- `SearchMode.RELAXED` — relaxed thresholds, broader queries, auto fallback

**NORMAL → RELAXED auto-fallback:** If `NORMAL` mode returns null, `searchAll()` automatically retries with `RELAXED` mode before giving up.

**Steps in `searchWithMode()` (line 119):**
1. **Clean queries** — `cleanQuery()` strips parenthesized suffixes, channel names
2. **Extract artist from filename** — When artist is "Desconhecido"/"<unknown>"
3. **Step 0: AcoustID fingerprint** — `AcoustIDService.searchByFile()` — almost always fails because API key `4m9Q2k9p` is invalid (HTTP 400)
4. **Step 1: iTunes Search API** — `searchItunes()` — Brazilian store (`country=BR`), scoring-based
5. **Step 2: MusicBrainz** — `searchMusicBrainz()` — detailed metadata with album art URLs
6. **RELAXED-only: Broader fallback queries** — If main search returned nothing in RELAXED mode:
   - Retry with **title only** (ignoring extracted artist, which might be wrong)
   - Retry with **artist only** (ignoring title noise)
7. **Merge results** — First non-null value per field wins
8. **Download album art** — Cover Art Archive first, then iTunes artwork fallback

### Retry Button
In `TagEditorActivity.showSearchConfirmation()` — the confirmation dialog now has a **"Tentar Novamente"** neutral button (only shown for NORMAL mode searches). When tapped:
1. Dismisses current dialog
2. Calls `searchOnline(SearchMode.RELAXED)` — uses relaxed thresholds and also tries title-only / artist-only queries
3. If RELAXED still fails, shows "Nada encontrado. Tente editar manualmente os campos e buscar novamente."

### SearchResult Data Class
```kotlin
data class SearchResult(
    val title: String?, val artist: String?, val album: String?,
    val year: String?, val genre: String?, val trackNumber: String?,
    val albumArtUrl: String?
)
```

### MusicMetadata Output
```kotlin
data class MusicMetadata(
    val title: String?, val artist: String?, val album: String?,
    val year: String?, val genre: String?, val trackNumber: String?,
    val albumArtBytes: ByteArray?, val albumArtMime: String?
) {
    val isComplete: Boolean  // title AND artist both non-null
}
```

---

## Filename Artist Extraction

### When artist is "Desconhecido" or "<unknown>"

**Strategy 1: Dash-separated** — `"Artist - Title - Channel.mp3"`
```kotlin
dashParts.last()  // ❌ OLD: returned channel name
dashParts.first() // ✅ CORRECT: returns artist
```

**Strategy 2: Double-space separated** — `"Title  Artist  Channel.mp3"`
```kotlin
// Split by \s{2,}, return 2nd segment
```

**Validation:** Segment must be 2-50 chars and contain at least one uppercase letter.

### URL Cleaning (`cleanQuery()`)
1. Remove file extension first
2. Strip trailing `- NameVEVO`, `- ChannelTV`, `- Channel`, etc.
3. Strip parenthesized content: `(youtube)`, `(official)`, `(audio)`, `(lyric video)`
4. Strip leading `-` or `|`

---

## iTunes Search (`searchItunes()`)

### URL
```
https://itunes.apple.com/search?term={encoded}&limit=5&country=BR
```

### Scoring Thresholds
| Mode | Condition | Min Score | Behavior |
|------|-----------|-----------|----------|
| NORMAL | Perfect match | 10 (or 5 if no artist) | Return immediately |
| NORMAL | Artist known + score | 5 | Best result |
| NORMAL | Artist blank + score | 3 | Best result |
| RELAXED | Perfect match | 8 (or 4 if no artist) | Return immediately |
| RELAXED | Artist known + score | 3 | Best result |
| RELAXED | Artist blank + score | 2 | Best result |
| Any | Below threshold | — | Return null |

### Scoring Rules
- Artist name exact match: **+8**
- Artist partial match (contains): **+5**
- Title word overlap (words >2 chars): **+3 per word**
- Album match: **+3**

### Critical Fix Applied
**ROOT CAUSE — iTunes returning unrelated results:** The old code returned the first iTunes result regardless of score. For "Savior Tye Tribbett & Tim Bush", iTunes BR returned "Three Little Birds / Bob Marley" as result #1 (score 0). **Fix:** Track the best score across all results and only return if minimum threshold is met. Perfect matches return immediately.

---

## MusicBrainz Search (`searchMusicBrainz()`)

### URL
```
https://musicbrainz.org/ws/2/recording/?query={lucene_query}&fmt=json&limit=3
```

### Lucene Query Format
```
recording:"title" artist:"artist" release:"album"
```

### Result Parsing
- Extract recording title, artist (from `artist-credit`), album (from first `release`)
- Extract year from release `date` (first 4 chars)
- Extract track number from release `media[0].track` by matching title
- **Album Art URL:** `https://coverartarchive.org/release/{releaseId}/front`

### Cover Art Archive Notes
- URL format: `https://coverartarchive.org/release/{mbid}/front`
- Always returns a 302 redirect to `https://archive.org/download/...`
- The redirect chain may fail with `FileNotFoundException` on the device if archive.org doesn't have the image
- **Fix:** Use explicit redirect following in download function (manual loop for 3xx codes)

---

## Album Art Download Pipeline

### Order of Attempts
1. Cover Art Archive (via `searchMusicBrainz` release MBID)
2. iTunes artwork search, country=BR (`searchItunesArtwork`)
3. iTunes artwork search, country=US (broader catalog fallback)

### `downloadFromUrl()` — Explicit Redirect Handling
```kotlin
val conn = URL(currentUrl).openConnection() as HttpURLConnection
conn.instanceFollowRedirects = false  // manual handling
conn.connect()
val code = conn.responseCode
if (code in 300..399) {
    val location = conn.getHeaderField("Location")
    currentUrl = if (location.startsWith("http")) location
                 else URL(URL(currentUrl), location).toString()
    // retry with new URL
}
```
Max 5 redirect attempts. Timeout: 10s per attempt. User-Agent: `MP3Player-Android/1.0`.

### `searchItunesArtwork()`
- Searches `https://itunes.apple.com/search?term={artist+album}&entity=album&limit=5&country={BR|US}`
- Scores results: exact artist match (+10), partial (+5), album match (+3)
- Resizes art URL: `100x100bb` → `600x600bb`
- Returns best URL with score >= 3, or null

---

## Custom AudioProcessor Wiring into ExoPlayer

To inject a custom `AudioProcessor` into ExoPlayer's audio pipeline without modifying library source:

### Approach: `MediaCodecAudioRenderer` with `AudioProcessor...` varargs

The `MediaCodecAudioRenderer` has a public constructor that accepts `AudioProcessor...`:

```kotlin
MediaCodecAudioRenderer(
    context,
    MediaCodecSelector.DEFAULT,
    handler,
    audioListener,
    AudioCapabilities.DEFAULT_AUDIO_CAPABILITIES,  // or getCapabilities(context)
    eqProc as AudioProcessor
)
```

### Integration via `RenderersFactory`

Override `ExoPlayer.Builder.setRenderersFactory()` to provide only the audio renderer with custom processor:

```kotlin
val renderersFactory = RenderersFactory { handler, videoListener, audioListener, textOutput, metadataOutput ->
    arrayOf(
        MediaCodecAudioRenderer(
            context,
            MediaCodecSelector.DEFAULT,
            handler,
            audioListener,
            AudioCapabilities.DEFAULT_AUDIO_CAPABILITIES,
            eqProc as AudioProcessor
        )
    )
}
exoPlayer = ExoPlayer.Builder(context)
    .setRenderersFactory(renderersFactory)
    .build()
```

**Notes:**
- This constructor is NOT annotated `@UnstableApi` (stable in Media3 1.2.1)
- The renderer internally creates a `DefaultAudioSink` with the given processors
- Works alongside the rest of ExoPlayer's pipeline (source, load control, etc.)
- If the app has video files, a `MediaCodecVideoRenderer` should also be included; for audio-only apps, omitting it is fine

### CRITICAL: `queueInput()` Must Advance Buffer Position

`AudioProcessor.queueInput()` **must** call `inputBuffer.position(inputBuffer.limit())` after processing. ExoPlayer's `DefaultAudioSink` checks `buffer.hasRemaining()` after `queueInput()` to determine if all data was consumed. Without this, ExoPlayer sees 0 bytes consumed → audio pipeline stalls → no sound.

```kotlin
override fun queueInput(inputBuffer: ByteBuffer) {
    // ... process all data ...
    inputBuffer.position(inputBuffer.limit())  // ← REQUIRED: signal "all consumed"
    // ... write processed output ...
}
```

### CRITICAL: Dynamic `isActive()`

`AudioProcessor.isActive()` is checked on every buffer cycle. If it returns `true`, all audio is routed through `queueInput()`. Must be dynamic:

```kotlin
@Volatile
private var isActiveState = false

override fun isActive(): Boolean = isActiveState

private fun updateActiveState() {
    // Only activate when there's actual processing to do
    isActiveState = preampGainDb != 0f || bands.any { it.gainDb != 0f }
}
```

At boot with all gains = 0, `isActive()` returns `false` → audio bypasses the processor entirely until the user adjusts EQ.

## Logcat Diagnostics

### Known Issue — MetadataSearch Logs Not Appearing
`Log.i/w` calls with tag `"MetadataSearch"` from `MetadataSearchService.kt` may not appear in logcat on MIUI, even though `AcoustID` logs (tag `"AcoustID"`) from the same process do appear. **Workaround:** Add Toast messages in UI code for visual feedback instead of relying on logcat.

```powershell
# Standard logcat
adb -s 100.64.71.9:5555 logcat -s AcoustID:* MetadataSearch:* *:S

# Full capture to file
adb -s 100.64.71.9:5555 logcat -v brief > logcat.txt

# Clear before capture
adb -s 100.64.71.9:5555 logcat -c
```

---

## Theme System (Skin)

The app has a theme/skin system with styles defined in `res/values/styles.xml`. Three themes:
- `AppTheme` (default — light)
- `AppTheme.Dark`
- `AppTheme.Blue`

Applied in `ui/theme/` via `SharedPreferences` key `"KEY_SKIN"`.

---

## SearchMode System

```kotlin
enum class SearchMode { NORMAL, RELAXED }
```

- **`NORMAL`** (default): Standard scoring thresholds (artist min 5, no-artist min 3). Strict queries with artist+title+album.
- **`RELAXED`**: Lower thresholds (artist min 3, no-artist min 2). Tries broader queries (title-only, artist-only) when main query fails.

Auto-fallback: If `searchAll()` is called with `NORMAL` and returns null, it automatically retries with `RELAXED`.

## Retry Button Flow

1. User taps "Buscar na Internet"
2. `searchOnline(SearchMode.NORMAL)` is called
3. If results found → dialog shows with "Aplicar", "Descartar", and **"Tentar Novamente"**
4. **"Tentar Novamente"** triggers `searchOnline(SearchMode.RELAXED)`:
   - Lower scoring thresholds
   - Broader MusicBrainz queries (no album filter, more results)
   - Falls back to title-only and artist-only searches
5. If RELAXED also fails → user sees "Tente editar manualmente os campos e buscar novamente"

## Known Issues & Fixes

| Issue | Root Cause | Fix | File:Line |
|-------|-----------|-----|-----------|
| Artist shows "Desconhecido" | YouTube MP3s have no ID3 tags | Extract artist from filename (first dash segment or second double-space segment) | `MetadataSearchService.kt:70` |
| Search returns wrong artist | iTunes BR returns irrelevant results | Scoring threshold system: NORMAL min=5/3, RELAXED min=3/2 | `MetadataSearchService.kt:308` |
| Album art not found | Cover Art Archive redirect to archive.org fails | Explicit redirect loop + iTunes artwork fallback with US store | `MetadataSearchService.kt:208` |
| Logs don't appear | MIUI logcat filtering | Toast messages as visual feedback | `TagEditorActivity.kt:245` |
| Filename ambiguity | Multiple filename formats | Try dash split first, then double-space split as fallback | `MetadataSearchService.kt:67` |
| AcoustID always fails | Invalid API key `4m9Q2k9p` (HTTP 400) | Accepted as non-critical; search falls through to iTunes/MusicBrainz | `AcoustIDService.kt:15` |
| First search returns nothing | Wrong artist extracted from filename, or title too noisy | Auto-fallback: NORMAL→RELAXED auto-retry; RELAXED tries title-only and artist-only queries | `MetadataSearchService.kt:110` |
| User sees wrong/short results | Scoring rejected borderline-but-correct match | User taps "Tentar Novamente" in dialog → triggers RELAXED mode with lower thresholds | `TagEditorActivity.kt:220` |
| **Audio stops / EQ not audible** | `EqualizerAudioProcessor.queueInput()` never calls `inputBuffer.position(inputBuffer.limit())` after processing. ExoPlayer sees 0 bytes consumed → audio pipeline stalls. Also `isActive()` was initially dynamic but ExoPlayer caches the `configure()` result — returning `false` at boot meant `queueInput()` was NEVER called after gains changed. | 1. Call `inputBuffer.position(inputBuffer.limit())` after successful processing. 2. Make `isActive()` always return `true`; use internal `isActiveState` flag to decide bypass vs processing inside `queueInput()`. | `EqualizerAudioProcessor.kt:95-116` |
| **Preset not persisting across sessions** | The preamp was baked into `currentGains[]` making it irreversible. `syncSoftwareEq()` passed preamp=0 to processor so preamp was never audible. | **Refactored:** `currentGains[]` now stores RAW gains only, `currentPreamp` is separate. `applyPreset()` no longer bakes preamp into gains. `syncSoftwareEq()` passes `currentPreamp` to processor. Added format version for backward compat. | `EqualizerFragment.kt:295-312` |
| **Preamp volume irreversible and cumulative** | `showVolumeDialog()` did `currentGains[i] += v` on already-baked gains. Each call added more, preamp could never be undone without reset. | Fixed by the same refactoring: preamp is now separate. `showVolumeDialog()` only updates `currentPreamp` and re-applies HW EQ bands without touching `currentGains[]`. | `EqualizerFragment.kt:407` |
| **Preamp not audible** | `syncSoftwareEq()` always called `mp.setEqPreampGain(0f)`, ignoring `currentPreamp`. The preamp was only baked into HW EQ gains, never sent to software EQ. | `syncSoftwareEq()` now calls `mp.setEqPreampGain(currentPreamp)` instead of `0f`. Software EQ receives preamp as a master multiplier. | `EqualizerFragment.kt:270` |
| **Duplicate mini-player on some screens** | `openNowPlaying()` could be called multiple times, adding duplicate fragments. | Added guard at start of `openNowPlaying()`: if backstack top is already "now_playing", return early. | `MainActivity.kt:634` |
| **EQ distorts audio at boost settings** | 20 cascaded peaking filters + preamp can push signal past 1.0. `coerceIn(-1f, 1f)` causes hard clipping distortion. | Replaced `coerceIn(-1f, 1f)` with `Math.tanh(sample)` — soft-clipping (tube-like saturation). Also made `isActive()` always return `true` to prevent ExoPlayer from caching the inactive state. | `EqualizerAudioProcessor.kt:131` |
| **Preset data corrupted on pt_BR locale** | `"%.1f".format(-4.0)` produces `"-4,0"` (comma decimal) on Brazilian locale. `joinToString(",")` uses same comma → data splits into 2x the expected parts. | Changed separator to `|` and format with `Locale.US`. `loadActivePreset()` detects old corrupted data (40+ parts) and reconstructs by pairing parts. | `EqualizerFragment.kt:340-356` |
| **EQ still distorts at high boost** | `tanh()` soft-clipping alone insufficient — 20 cascaded peaking filters + preamp can produce cumulative gain >> 6 dB at certain frequencies, exceeding `tanh()` saturation threshold. | Added peak limiter in `queueInput()`: measure peak after filter cascade, apply gain reduction (1.0/peak) with per-sample attack/release smoothing (1ms attack, 100ms release). `tanh()` remains as final safety net only. | `EqualizerAudioProcessor.kt:167-183` |
| **No EQ on/off button** | User had no way to bypass EQ without resetting all gains to zero. | Added `enabled` flag in `EqualizerAudioProcessor`, `setEnabled()` method, `Switch` widget in fragment header (default ON). Toggle disables both HW and SW EQ. | `EqualizerAudioProcessor.kt:53-56`, `EqualizerFragment.kt:162-173` |
| **No visual limiting feedback** | User couldn't see when limiter was active or how much reduction was applied. | Added `gainReductionDb` property on processor, `TextView` indicator in bottom bar (green=no reduction, yellow=moderate, red=heavy), polled every 250ms via Handler. | `EqualizerAudioProcessor.kt:58-62`, `EqualizerFragment.kt:175-185` |
| **EQ state not persisted** | EQ enabled/disabled state not saved to SharedPreferences — switch reset to ON on every restart. | Added `KEY_ENABLED` to `saveActivePreset()`/`loadActivePreset()`. Uses `restoringEqState` flag to prevent listener firing during restoration. | `EqualizerFragment.kt:162-173` |
| **No most-played tracking** | App had no mechanism to count or sort by play frequency. | Added `PlayCountManager` (JSON in SharedPreferences), increment on `playSongFromList()`, `SortMode.PLAY_COUNT` in `SongAdapter.sortSongs()`, "Mais Tocadas" option in sort dialog. | `data/PlayCountManager.kt`, `MainActivity.kt:393`, `SongsFragment.kt:58` |
| **EQ only applies after opening fragment** | Saved gains/preamp never loaded into processor until `EqualizerFragment.loadActivePreset()` runs. Playing a song without opening EQ meant processor stayed flat. | Added `EqStateLoader.restoreTo()` — loads same SharedPreferences used by fragment and applies to processor. Called in `playSongFromList()` before playing. | `data/EqStateLoader.kt`, `MainActivity.kt:397` |
| **EQ deactivates on song change** | `AudioProcessor.reset()` set `isActiveState = false` and `configure()` never recalculated it. ExoPlayer calls `reset()` between songs → processor silently bypassed. | Added `updateActiveState()` call in `configure()` and `reset()`. Removed `isActiveState = false` from `reset()` — state is now always recalculated from actual gains/enabled. | `EqualizerAudioProcessor.kt:107,133` |
| **EQ toggle button not visible** | `Switch` widget may not render correctly on some MIUI versions or was too small to notice. | Replaced `Switch` with `Button` styled as toggle (`EQ ON`/`EQ OFF`), matching existing button styles (`bg_preset_active`/`bg_preset_btn`). Uses `isSelected` for state. | `EqualizerFragment.kt:162-176` |
| **Obscure songs not found** | iTunes/MusicBrainz don't have gospel/indie/obscure tracks | Added `searchYouTube()` fallback — parses ytInitialData from YouTube search page. Returns video title + channel name as song/artist. Last resort after all API searches. | `MetadataSearchService.kt:550-610` |
| **Artist not extracted from (feat. X)** | `extractArtistFromFilename()` only tried dash and double-space patterns. "Title (feat. Artist).mp3" had no dash → artist stayed blank. | Added feat/ft regex: `\(?(?:feat|ft)[.\s]+(.+?)\)?`. Extracts "Ife Darams" from "The Father's Love Medley (feat. Ife Darams)". | `MetadataSearchService.kt:87-93` |
| **Title still contains artist prefix** | When artist extracted from filename in `loadCurrentMetadata()`, the prefix wasn't stripped from title. "Tye Tribbett - Savior" kept the full string. | After extracting artist, also strip it from title using regex: `^Artist\s*[-–—|]\s*`. | `TagEditorActivity.kt:141-147` |
| **Search overwrites known-good fields** | `searchOnline()` replaced ALL fields with search results, even when existing data (from filename) was correct. | Merge: track `known*` booleans per field. Only use search result for fields that are currently unknown/Desconhecido. Dialog shows "(mantido)" vs "(novo!)". | `TagEditorActivity.kt:197-233`, `TagEditorActivity.kt:257-308` |
| **Repository path wrong** | SKILL.md had `Codigos\Mp3Player` but real project is at `Codigos\Android\Mp3Player` | Updated SKILL.md path. Caused stale .cxx cache with hardcoded old paths. | `SKILL.md:12` |
| **Songs list empty after theme toggle** | `savedInstanceState == null` guard blocked `checkAndRequestPermissions()` → `loadSongs()` on recreation. `recreate()` sets `savedInstanceState` non-null, so permission check + song load was skipped entirely. | Removed the `if (savedInstanceState == null)` guard — always call `checkAndRequestPermissions()`. Safe because granted permission just calls `loadSongs()`, no dialog. | `MainActivity.kt:193` |
| **NowPlayingFragment duplicates on rapid tap** | `openNowPlaying()` uses `FragmentTransaction.commit()` which is async — backstack not updated immediately. Tapping mini player twice quickly bypasses the backstack guard, creating duplicate fragments. | Added `nowPlayingPending` flag + `executePendingTransactions()` after `commit()` to ensure synchronous execution before visibility changes. | `MainActivity.kt:100,640-663` |
| **Mini player below BottomNav (perceived duplicate)** | `playerPanel` was placed AFTER `BottomNavigationView` in `activity_main.xml`. The mini player appeared literally under the bottom nav bar, making it look like a redundant "third" player. | Moved `playerPanel` + divider ABOVE `BottomNavigationView` so it sits between content and bottom nav (standard music player layout). | `activity_main.xml:40-51` |
| **NowPlayingFragment stops opening after tab switch** | `switchFragment()` used `replace().commitNow()` without clearing backstack. If user opens NowPlaying (backstack: `"now_playing"`), then switches tabs, the stale backstack entry persisted. Tapping mini player later called `openNowPlaying()` guard which saw `"now_playing"` on backstack and **blocked** — NowPlaying could never reopen. | Added `popBackStackImmediate(null, POP_BACK_STACK_INCLUSIVE)` at start of `switchFragment()` to clear all stale backstack entries before replacing fragment. | `MainActivity.kt:362` |
| **Player panel stays hidden after tab switch** | `syncViewVisibility()` was never called after tab switch because backstack didn't change (only the fragment was replaced). So `playerPanel.visibility` stayed `GONE` from the previous `openNowPlaying()` call. | Added `syncViewVisibility()` call after `commitNow()` in `switchFragment()` to re-evaluate and restore correct panel visibility. | `MainActivity.kt:365` |
| **Mini player appears while NowPlaying is open** | `playSongFromList()` unconditionally set `playerPanel.visibility = View.VISIBLE`. When user pressed next/prev or song auto-advanced while NowPlayingFragment was shown (backstack: `"now_playing"`), the mini player would become visible and stay visible because `syncViewVisibility()` was never called afterward. | Replaced unconditional `playerPanel.visibility = View.VISIBLE` with `syncViewVisibility()` call, which checks backstack state and only shows panel when "now_playing" is not on top. | `MainActivity.kt:394-395` |
| **Mini player appears while NowPlaying is open** | `playSongFromList()` unconditionally set `playerPanel.visibility = View.VISIBLE`. When user pressed next/prev or song auto-advanced while NowPlayingFragment was shown (backstack: `"now_playing"`), the mini player would become visible and stay visible because `syncViewVisibility()` was never called afterward. | Replaced unconditional `playerPanel.visibility = View.VISIBLE` with `syncViewVisibility()` call, which checks backstack state and only shows panel when "now_playing" is not on top. | `MainActivity.kt:394-395` |

---

## ADB Workflow

```powershell
# Connect WiFi
adb tcpip 5555
adb connect 100.64.71.9:5555

# Install
adb -s 100.64.71.9:5555 install -r app-debug.apk

# Force stop
adb shell am force-stop com.mp3player.debug

# Clear data
adb shell pm clear com.mp3player.debug

# View logs (filtered)
adb logcat -s AcoustID:* MetadataSearch:* *:S

# Uninstall
adb uninstall com.mp3player.debug
```

---

## How to Evolve This Knowledge

When you discover a new issue, fix, or pattern in this project, update this skill file with:
1. The issue description and root cause
2. The fix applied (file, line, code pattern)
3. Why it works (so the reasoning is preserved)
4. The "Known Issues & Fixes" table updated

This ensures every session builds on the accumulated knowledge rather than starting from scratch.
