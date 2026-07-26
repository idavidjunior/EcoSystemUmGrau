package com.mp3player.data.online

import android.content.Context
import android.util.Log
import com.mp3player.data.model.MusicMetadata
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.regex.Pattern

data class SearchResult(
    val title: String?,
    val artist: String?,
    val album: String?,
    val year: String?,
    val genre: String?,
    val trackNumber: String?,
    val albumArtUrl: String?
)

enum class SearchMode { NORMAL, RELAXED }

object MetadataSearchService {

    private const val TAG = "MetadataSearch"
    private const val TIMEOUT_MS = 10000

    /** Strip common filename noise from search queries */
    fun cleanQuery(raw: String): String {
        if (raw.isBlank()) return ""
        var s = raw
            .removeSuffix(".mp3").removeSuffix(".flac").removeSuffix(".ogg").removeSuffix(".wav")
            .removeSuffix(".m4a").removeSuffix(".wma")
        // Remove parenthesized noise only
        s = s.replace(Regex("""\s*\([^)]*(youtube|vevo|official|lyric|clipe|hd|hq|4k|groove|gospel|beats|isa[ií]as|saulo)[^)]*\)""", RegexOption.IGNORE_CASE), "")
        // Remove bracketed noise
        val noiseKeywords = listOf("youtube", "vevo", "official", "lyric", "clipe", "hd", "hq", "4k",
            "groove", "gospel", "beats", "isaías", "isaias", "serie", "série", "hits")
        var bi = s.indexOf('[')
        while (bi >= 0) {
            val ei = s.indexOf(']', bi)
            if (ei >= 0) {
                val inner = s.substring(bi, ei + 1)
                if (noiseKeywords.any { inner.contains(it, ignoreCase = true) }) {
                    s = s.replace(inner, "")
                    bi = s.indexOf('[', bi)
                } else {
                    bi = s.indexOf('[', ei)
                }
            } else break
        }
        // Remove emoji / special chars
        s = s.replace(Regex("""[♫♪🎵🎶🔥✝️🙏👆🏻✔️🔴🟢🔵⭐💥💫✨>]+"""), " ")
        // Strip trailing separators
        s = s.replace(Regex("""\s*[-–—|]+\s*$"""), "")
        // Remove trailing channel-like segment from YouTube downloads
        s = s.replace(Regex("""\s*[-–—|]\s*\w{2,}(?:VEVO|TV|official|channel|youtube|live)\w*\s*$""", RegexOption.IGNORE_CASE), "")
        // Collapse whitespace
        s = s.replace(Regex("\\s+"), " ").trim()
        if (s.length > 60) s = s.take(60).trim()
        return s
    }

    /** Try to extract artist name from common filename patterns when artist is unknown.
     * Conventions: "Artist - Title" or "Title  Artist  Channel" (YouTube downloads) or
     * "Title (feat. Artist)" / "Title (ft. Artist)".
     * Uses dash patterns first; falls back to feat/ft patterns, then double-space patterns. */
    fun extractArtistFromFilename(filename: String): String? {
        val name = filename.substringAfterLast('/').substringBeforeLast('.')
        // Try dash-separated: "Artist - Title"
        val dashParts = name.split(Regex("\\s*[-–—|]\\s*"))
        if (dashParts.size >= 2) {
            val first = dashParts.first().trim()
            if (first.length in 2..50 && first.any { it.isUpperCase() }) {
                return first
            }
        }
        // Try feat/ft pattern: "Title (feat. Artist)" or "Title (ft. Artist)"
        val featMatch = Regex("""\(?(?:feat|ft)[.\s]+(.+?)\)?""", RegexOption.IGNORE_CASE).find(name)
        if (featMatch != null) {
            val artist = featMatch.groupValues[1].trim().removeSuffix(")")
            if (artist.length in 2..50 && artist.any { it.isUpperCase() }) {
                return artist
            }
        }
        // Fallback: space-separated: "Title  Artist  Channel" (artist is 2nd segment)
        val spaceParts = name.split(Regex("\\s{2,}"))
        if (spaceParts.size >= 3) {
            val second = spaceParts[1].trim()
            if (second.length in 2..50 && second.any { it.isUpperCase() }) {
                return second
            }
        }
        return null
    }

    suspend fun searchAll(songTitle: String, songArtist: String, songAlbum: String, filePath: String? = null, context: Context? = null, mode: SearchMode = SearchMode.NORMAL): MusicMetadata? {
        return withContext(Dispatchers.IO) {
            var titleClean = cleanQuery(songTitle)
            var artistClean = if (songArtist == "Desconhecido" || songArtist == "<unknown>") "" else cleanQuery(songArtist)
            var albumClean = if (songAlbum == "Desconhecido" || songAlbum == "<unknown>") "" else cleanQuery(songAlbum)

            // Try to extract artist from filename if unknown
            if (artistClean.isBlank() && filePath != null) {
                val extracted = extractArtistFromFilename(filePath)
                if (extracted != null) {
                    artistClean = cleanQuery(extracted)
                    titleClean = cleanQuery(songTitle.replace(Regex("^" + Pattern.quote(extracted) + "\\s*[-–—|]\\s*", RegexOption.IGNORE_CASE), ""))
                    Log.i(TAG, "Extracted artist '$artistClean' from filePath, title='$titleClean'")
                }
            }

            if (titleClean.isBlank() && artistClean.isBlank()) return@withContext null

            // Try current mode, then fallback to RELAXED if NORMAL found nothing
            val result = searchWithMode(titleClean, artistClean, albumClean, filePath, context, mode)
            if (result != null || mode == SearchMode.RELAXED) return@withContext result

            // NORMAL mode failed — auto-retry with RELAXED
            Log.i(TAG, "NORMAL search found nothing, retrying with RELAXED mode")
            searchWithMode(titleClean, artistClean, albumClean, filePath, context, SearchMode.RELAXED)
        }
    }

    private suspend fun searchWithMode(titleClean: String, artistClean: String, albumClean: String, filePath: String?, context: Context?, mode: SearchMode): MusicMetadata? {
        val results = mutableListOf<SearchResult>()

        // 0. AcoustID audio fingerprint (most accurate when file is available)
        if (filePath != null && context != null) {
            try {
                val acoustIdResult = AcoustIDService.searchByFile(filePath, context)
                if (acoustIdResult != null) {
                    val title = if (acoustIdResult.title?.isNotBlank() == true) acoustIdResult.title else null
                    val artist = if (acoustIdResult.artist?.isNotBlank() == true) acoustIdResult.artist else null
                    val album = if (acoustIdResult.album?.isNotBlank() == true) acoustIdResult.album else null
                    val year = if (acoustIdResult.year?.isNotBlank() == true) acoustIdResult.year else null
                    val genre = if (acoustIdResult.genre?.isNotBlank() == true) acoustIdResult.genre else null
                    if (title != null || artist != null || album != null) {
                        Log.i(TAG, "AcoustID result: $title / $artist / $album")
                        results.add(SearchResult(title, artist, album, year, genre, null, null))
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "AcoustID search failed: ${e.message}")
            }
        }

        // 1. iTunes Search API (fast, has art)
        try {
            val r = searchItunes(titleClean, artistClean, albumClean, mode)
            if (r != null) results.add(r)
        } catch (e: Exception) {
            Log.w(TAG, "iTunes search failed: ${e.message}")
        }

        // 2. MusicBrainz (detailed)
        try {
            val r = searchMusicBrainz(titleClean, artistClean, albumClean, mode)
            if (r != null) results.add(r)
        } catch (e: Exception) {
            Log.w(TAG, "MusicBrainz search failed: ${e.message}")
        }

        // If main queries returned nothing and RELAXED mode, try broader queries
        if (results.isEmpty() && mode == SearchMode.RELAXED) {
            // Try title-only search (sometimes artist value is wrong)
            if (titleClean.isNotBlank() && artistClean.isNotBlank()) {
                try {
                    val r = searchItunes(titleClean, "", "", mode)
                    if (r != null) results.add(r)
                } catch (e: Exception) { }
                try {
                    val r = searchMusicBrainz(titleClean, "", "", mode)
                    if (r != null) results.add(r)
                } catch (e: Exception) { }
            }
            // Try artist-only search (sometimes title is wrong)
            if (results.isEmpty() && artistClean.isNotBlank()) {
                try {
                    val r = searchItunes("", artistClean, "", mode)
                    if (r != null) results.add(r)
                } catch (e: Exception) { }
                try {
                    val r = searchMusicBrainz("", artistClean, "", mode)
                    if (r != null) results.add(r)
                } catch (e: Exception) { }
            }
        }

        // Last resort: search YouTube (has obscure gospel, covers, and indie tracks)
        if (results.isEmpty()) {
            val youtubeQuery = buildList {
                if (titleClean.isNotBlank()) add(titleClean)
                if (artistClean.isNotBlank() && !titleClean.contains(artistClean, ignoreCase = true)) add(artistClean)
            }.joinToString(" ")
            if (youtubeQuery.isNotBlank()) {
                try {
                    val r = searchYouTube(youtubeQuery)
                    if (r != null) results.add(r)
                } catch (e: Exception) {
                    Log.w(TAG, "YouTube fallback failed: ${e.message}")
                }
            }
        }

        // Merge results - prefer first non-null per field
        if (results.isEmpty()) return null

        var title: String? = null
        var artist: String? = null
        var album: String? = null
        var year: String? = null
        var genre: String? = null
        var trackNumber: String? = null
        var artUrl: String? = null

        for (r in results) {
            if (title == null && r.title != null) title = r.title
            if (artist == null && r.artist != null) artist = r.artist
            if (album == null && r.album != null) album = r.album
            if (year == null && r.year != null) year = r.year
            if (genre == null && r.genre != null) genre = r.genre
            if (trackNumber == null && r.trackNumber != null) trackNumber = r.trackNumber
            if (artUrl == null && r.albumArtUrl != null) artUrl = r.albumArtUrl
        }

        // Download album art
        var artBytes: ByteArray? = null
        var artMime = "image/jpeg"
        fun downloadFromUrl(url: String): Boolean {
            return try {
                var currentUrl = url
                var attempts = 0
                val maxAttempts = 5
                while (attempts < maxAttempts) {
                    attempts++
                    val conn = URL(currentUrl).openConnection() as HttpURLConnection
                    conn.connectTimeout = TIMEOUT_MS
                    conn.readTimeout = TIMEOUT_MS
                    conn.doInput = true
                    conn.instanceFollowRedirects = false
                    conn.setRequestProperty("User-Agent", "MP3Player-Android/1.0")
                    conn.connect()
                    val code = conn.responseCode
                    if (code in 300..399) {
                        val location = conn.getHeaderField("Location")
                        conn.disconnect()
                        if (location == null) { Log.w(TAG, "Redirect with no Location"); return false }
                        currentUrl = if (location.startsWith("http")) location else URL(URL(currentUrl), location).toString()
                        Log.i(TAG, "Redirect $attempts -> $currentUrl")
                        continue
                    }
                    if (code != 200) {
                        Log.w(TAG, "HTTP $code for $currentUrl"); conn.disconnect(); return false
                    }
                    val stream = conn.inputStream
                    val baos = ByteArrayOutputStream()
                    stream.copyTo(baos)
                    artBytes = baos.toByteArray()
                    stream.close()
                    conn.disconnect()
                    artMime = conn.contentType ?: "image/jpeg"
                    return true
                }
                Log.w(TAG, "Too many redirects for $url")
                false
            } catch (e: Exception) {
                Log.w(TAG, "Failed to download art from $url: ${e.javaClass.simpleName}: ${e.message?.take(80)}")
                false
            }
        }

        // Try Cover Art Archive first
        if (artUrl != null) {
            downloadFromUrl(artUrl)
        }

        // Fallback: search iTunes for artwork using artist+album
        if (artBytes == null && artist != null && album != null) {
            val artUrl2 = searchItunesArtwork(artist, album)
            if (artUrl2 != null) {
                downloadFromUrl(artUrl2)
            }
        }

        // Last resort fallback: search iTunes with artist only
        if (artBytes == null && artist != null && album == null) {
            val artUrl2 = searchItunesArtwork(artist, null)
            if (artUrl2 != null) {
                downloadFromUrl(artUrl2)
            }
        }

        return MusicMetadata(
            title = title?.ifBlank { null },
            artist = artist?.ifBlank { null },
            album = album?.ifBlank { null },
            year = year?.ifBlank { null },
            genre = genre?.ifBlank { null },
            trackNumber = trackNumber?.ifBlank { null },
            albumArtBytes = artBytes,
            albumArtMime = artMime
        )
    }

    private fun httpGet(urlString: String): String? {
        var conn: HttpURLConnection? = null
        return try {
            conn = URL(urlString).openConnection() as HttpURLConnection
            conn.connectTimeout = TIMEOUT_MS
            conn.readTimeout = TIMEOUT_MS
            conn.requestMethod = "GET"
            conn.setRequestProperty("User-Agent", "MP3Player-Android/1.0")
            conn.connect()
            val code = conn.responseCode
            if (code != 200) {
                Log.w(TAG, "HTTP $code for $urlString")
                null
            } else {
                conn.inputStream.bufferedReader().readText()
            }
        } catch (e: Exception) {
            Log.w(TAG, "HTTP error: ${e.message} for $urlString")
            null
        } finally {
            conn?.disconnect()
        }
    }

    private fun searchItunes(title: String, artist: String, album: String, mode: SearchMode = SearchMode.NORMAL): SearchResult? {
        val term = buildList {
            if (title.isNotBlank()) add(title)
            if (artist.isNotBlank()) add(artist)
            if (album.isNotBlank()) add(album)
        }.joinToString(" ")
        if (term.isBlank()) return null

        val encoded = URLEncoder.encode(term, "UTF-8")
        val url = "https://itunes.apple.com/search?term=$encoded&entity=song&limit=5&country=BR"
        val json = httpGet(url) ?: return null

        val root = JSONObject(json)
        val results = root.optJSONArray("results") ?: return null
        if (results.length() == 0) return null

        val titleWords = title.lowercase().split(Regex("\\s+")).filter { it.length > 2 }.toSet()

        // Try to find the best match
        var bestResult: SearchResult? = null
        var bestScore = -1

        for (i in 0 until results.length()) {
            val item = results.getJSONObject(i)
            val trackName = item.optString("trackName", "").ifBlank { null }
            val artistName = item.optString("artistName", "").ifBlank { null }
            val collectionName = item.optString("collectionName", "").ifBlank { null }
            val releaseDate = item.optString("releaseDate", "").take(4).ifBlank { null }
            val primaryGenre = item.optString("primaryGenreName", "").ifBlank { null }
            val trackNumber = item.optInt("trackNumber", -1).let { if (it > 0) it.toString() else null }
            val artUrl = item.optString("artworkUrl100", "").ifBlank { null }
                ?.replace("100x100bb", "600x600bb")

            // Score this result
            var score = 0

            // Artist exact match = strong signal
            if (artist.isNotBlank() && artistName != null &&
                artist.lowercase() == artistName.lowercase()) score += 10

            // Artist partial match
            if (artist.isNotBlank() && artistName != null &&
                artistName.lowercase().contains(artist.lowercase())) score += 5

            // Title word overlap
            if (trackName != null && titleWords.isNotEmpty()) {
                val titleWordsResult = trackName.lowercase().split(Regex("\\s+")).filter { it.length > 2 }.toSet()
                val overlap = titleWords.intersect(titleWordsResult).size
                score += overlap * 3
            }

            // Album match
            if (album.isNotBlank() && collectionName != null &&
                collectionName.lowercase().contains(album.lowercase())) score += 3

            val result = SearchResult(
                title = trackName,
                artist = artistName,
                album = collectionName,
                year = releaseDate,
                genre = primaryGenre,
                trackNumber = trackNumber,
                albumArtUrl = artUrl
            )

            // Return immediately for perfect/excellent match
            val perfectThreshold = if (mode == SearchMode.RELAXED) 8 else 10
            val noArtistPerfectThreshold = if (mode == SearchMode.RELAXED) 4 else 5
            if (score >= perfectThreshold || (artist.isBlank() && score >= noArtistPerfectThreshold)) {
                return result
            }

            // Track best result for borderline cases
            if (score > bestScore) {
                bestScore = score
                bestResult = result
            }
        }

        // Return best result only if it has at least minimal relevance
        val minScore = if (artist.isNotBlank()) {
            if (mode == SearchMode.RELAXED) 3 else 5
        } else {
            if (mode == SearchMode.RELAXED) 2 else 3
        }
        if (bestScore >= minScore) {
            return bestResult
        }

        return null
    }

    private fun searchMusicBrainz(title: String, artist: String, album: String, mode: SearchMode = SearchMode.NORMAL): SearchResult? {
        // RELAXED mode: use simpler query for broader matches
        val query = if (mode == SearchMode.RELAXED) {
            buildString {
                if (title.isNotBlank()) append("recording:\"${title.replace("\"", "")}\" ")
                if (artist.isNotBlank()) append("AND artist:\"${artist.replace("\"", "")}\" ")
            }.trim()
        } else {
            buildString {
                if (title.isNotBlank()) append("recording:\"${title.replace("\"", "")}\" ")
                if (artist.isNotBlank()) append("AND artist:\"${artist.replace("\"", "")}\" ")
                if (album.isNotBlank()) append("AND release:\"${album.replace("\"", "")}\" ")
            }.trim()
        }

        if (query.isBlank()) return null

        val encoded = URLEncoder.encode(query, "UTF-8")
        val limit = if (mode == SearchMode.RELAXED) 5 else 3
        val url = "https://musicbrainz.org/ws/2/recording/?query=$encoded&fmt=json&limit=$limit"
        val json = httpGet(url) ?: return null

        val root = JSONObject(json)
        val recordings = root.optJSONArray("recordings") ?: return null
        if (recordings.length() == 0) return null

        val recording = recordings.getJSONObject(0)
        val recordingTitle = recording.optString("title", "").ifBlank { null }

        // Get artist
        val artistCredits = recording.optJSONArray("artist-credit")
        var recordingArtist: String? = null
        if (artistCredits != null && artistCredits.length() > 0) {
            val first = artistCredits.getJSONObject(0)
            val artistObj = first.optJSONObject("artist")
            if (artistObj != null) {
                recordingArtist = artistObj.optString("name", "").ifBlank { null }
            }
        }

        var recordingAlbum: String? = null
        var recordingYear: String? = null
        var coverArtUrl: String? = null
        val releases = recording.optJSONArray("releases")
        if (releases != null && releases.length() > 0) {
            val release = releases.getJSONObject(0)
            recordingAlbum = release.optString("title", "").ifBlank { null }
            val date = release.optString("date", "")
            recordingYear = date.take(4).ifBlank { null }
            val releaseId = release.optString("id", "")
            coverArtUrl = if (releaseId.isNotBlank()) "https://coverartarchive.org/release/$releaseId/front" else null

            // Try to get track number
            val media = release.optJSONArray("media")
            if (media != null && media.length() > 0) {
                val tracks = media.getJSONObject(0).optJSONArray("track")
                if (tracks != null) {
                    for (i in 0 until tracks.length()) {
                        val track = tracks.getJSONObject(i)
                        val trackTitle = track.optString("title", "")
                        if (trackTitle.lowercase() == (recordingTitle ?: title).lowercase()) {
                            val pos = track.optInt("position", -1)
                            if (pos > 0) {
                                val number = track.optString("number", pos.toString())
                                return SearchResult(
                                    title = recordingTitle,
                                    artist = recordingArtist,
                                    album = recordingAlbum,
                                    year = recordingYear,
                                    genre = null,
                                    trackNumber = number,
                                    albumArtUrl = coverArtUrl
                                )
                            }
                        }
                    }
                    // Fallback: use first track's position
                    val firstTrack = tracks.getJSONObject(0)
                    val pos = firstTrack.optInt("position", -1)
                    if (pos > 0) {
                        return SearchResult(
                            title = recordingTitle,
                            artist = recordingArtist,
                            album = recordingAlbum,
                            year = recordingYear,
                            genre = null,
                            trackNumber = pos.toString(),
                            albumArtUrl = coverArtUrl
                        )
                    }
                }
            }
        }

        return SearchResult(
            title = recordingTitle,
            artist = recordingArtist,
            album = recordingAlbum,
            year = recordingYear,
            genre = null,
            trackNumber = null,
            albumArtUrl = coverArtUrl
        )
    }

    /** Fallback search: query YouTube and extract title + channel as song/artist metadata.
     * Parses the ytInitialData JSON embedded in the YouTube search results page. */
    private fun searchYouTube(query: String): SearchResult? {
        if (query.isBlank()) return null
        try {
            val encoded = URLEncoder.encode(query, "UTF-8")
            val url = "https://www.youtube.com/results?search_query=$encoded"
            Log.i(TAG, "YouTube search: $url")
            val html = httpGet(url) ?: return null

            val dataMatch = Regex("""ytInitialData\s*=\s*(\{.+?\});\s*</script>""").find(html) ?: run {
                Log.w(TAG, "YouTube: no ytInitialData found in page")
                return null
            }
            val json = JSONObject(dataMatch.groupValues[1])
            val contents = json.getJSONObject("contents")
                .getJSONObject("twoColumnSearchResultsRenderer")
                .getJSONObject("primaryContents")
                .getJSONObject("sectionListRenderer")
                .getJSONArray("contents")
            // Find the itemSectionRenderer (may be at offset 0 or 1 due to ad/promo)
            var itemsArray: JSONArray? = null
            for (i in 0 until contents.length()) {
                try {
                    val sec = contents.getJSONObject(i)
                    if (sec.has("itemSectionRenderer")) {
                        itemsArray = sec.getJSONObject("itemSectionRenderer").getJSONArray("contents")
                        break
                    }
                } catch (_: Exception) {}
            }
            if (itemsArray == null) { Log.w(TAG, "YouTube: no itemSectionRenderer"); return null }

            for (i in 0 until itemsArray.length()) {
                try {
                    val item = itemsArray.getJSONObject(i)
                    if (!item.has("videoRenderer")) continue
                    val video = item.getJSONObject("videoRenderer")
                    val title = video.getJSONObject("title")
                        .getJSONArray("runs")
                        .getJSONObject(0)
                        .optString("text", "").ifBlank { null } ?: video.optString("title", "").ifBlank { null }
                    val channel = video.getJSONObject("ownerText")
                        .getJSONArray("runs")
                        .getJSONObject(0)
                        .optString("text", "").ifBlank { null } ?: video.optString("ownerText", "").ifBlank { null }
                    if (title != null && channel != null) {
                        Log.i(TAG, "YouTube result: title='$title' channel='$channel'")
                        return SearchResult(
                            title = cleanQuery(title),
                            artist = cleanQuery(channel),
                            album = null, year = null, genre = null, trackNumber = null, albumArtUrl = null
                        )
                    }
                } catch (_: Exception) {}
            }
            Log.w(TAG, "YouTube: no video results parsed")
        } catch (e: Exception) {
            Log.w(TAG, "YouTube search failed: ${e.message}")
        }
        return null
    }

    /** Search iTunes for album art using artist and/or album name. Returns art URL or null. */
    private fun searchItunesArtwork(artist: String, album: String?): String? {
        if (artist.isBlank()) return null
        val term = buildList {
            add(artist)
            if (album?.isNotBlank() == true) add(album)
        }.joinToString(" ")
        if (term.isBlank()) return null

        // Try BR first, then US (broader catalog)
        for (country in listOf("BR", "US")) {
            val encoded = URLEncoder.encode(term, "UTF-8")
            val url = "https://itunes.apple.com/search?term=$encoded&entity=album&limit=5&country=$country"
            val json = httpGet(url)
            if (json == null) {
                Log.w(TAG, "Artwork search HTTP failed for '$term' country=$country")
                continue
            }

            val root = JSONObject(json)
            val results = root.optJSONArray("results") ?: continue
            if (results.length() == 0) {
                Log.i(TAG, "Artwork search: no results for '$term' country=$country")
                continue
            }

            val artistLower = artist.lowercase()
            var bestScore = -1
            var bestArtUrl: String? = null

            for (i in 0 until results.length()) {
                val item = results.getJSONObject(i)
                val itemArtist = item.optString("artistName", "").lowercase()
                val itemAlbum = item.optString("collectionName", "").lowercase()
                var score = 0

                if (itemArtist == artistLower) score += 10
                if (itemArtist.contains(artistLower) || artistLower.contains(itemArtist)) score += 5
                if (album != null && itemAlbum.contains(album.lowercase())) score += 3
                if (album != null && itemArtist.contains(artistLower) && itemAlbum.contains(album.lowercase())) score += 5

                val artUrl = item.optString("artworkUrl100", "").ifBlank { null }
                    ?.replace("100x100bb", "600x600bb")
                if (artUrl != null && score > bestScore) {
                    bestScore = score
                    bestArtUrl = artUrl
                }
            }

            Log.i(TAG, "Artwork search for '$term' country=$country: bestScore=$bestScore, hasUrl=${bestArtUrl != null}")
            if (bestScore >= 3 && bestArtUrl != null) return bestArtUrl
        }

        return null
    }
}
