package com.mp3player.data.online

import android.util.Log
import com.mp3player.data.model.MusicMetadata
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

object AcoustIDService {

    private const val TAG = "AcoustID"
    private const val ACOUSTID_API_KEY = "4m9Q2k9p"
    private const val TIMEOUT_MS = 15000

    private var nativeLoaded = false

    init {
        try {
            System.loadLibrary("fingerprint_jni")
            nativeLoaded = true
            Log.i(TAG, "Native fingerprint library loaded")
        } catch (e: UnsatisfiedLinkError) {
            Log.w(TAG, "Native library not available, AcoustID disabled: ${e.message}")
        }
    }

    private external fun generateFingerprint(pcmData: ByteArray, sampleRate: Int, numChannels: Int): String

    suspend fun searchByFile(filePath: String, context: android.content.Context): MusicMetadata? = withContext(Dispatchers.IO) {
        if (!nativeLoaded) {
            Log.w(TAG, "Native library not loaded, skipping AcoustID")
            return@withContext null
        }

        val decoded = AudioDecoder.decodeToPcm(filePath) ?: run {
            Log.w(TAG, "Failed to decode audio to PCM")
            return@withContext null
        }

        Log.i(TAG, "Decoded ${decoded.pcm.size} bytes, ${decoded.durationSeconds}s at ${decoded.sampleRate}Hz")

        if (decoded.durationSeconds < 5) {
            Log.w(TAG, "Audio too short (${decoded.durationSeconds}s), need at least 5s")
            return@withContext null
        }

        val fingerprint = generateFingerprint(decoded.pcm, decoded.sampleRate, decoded.channels)
        if (fingerprint.isBlank()) {
            Log.w(TAG, "Fingerprint generation returned empty")
            return@withContext null
        }

        Log.i(TAG, "Fingerprint: ${fingerprint.take(40)}...")

        lookupAcoustId(fingerprint, decoded.durationSeconds.toInt())
    }

    private fun lookupAcoustId(fingerprint: String, duration: Int): MusicMetadata? {
        val url = "https://api.acoustid.org/v2/lookup"
        val params = buildString {
            append("client=").append(ACOUSTID_API_KEY)
            append("&fingerprint=").append(URLEncoder.encode(fingerprint, "UTF-8"))
            append("&duration=").append(duration)
            append("&meta=recordings+releases+releasegroups+compress")
        }

        val json = httpPost(url, params) ?: return null

        val root = JSONObject(json)
        val status = root.optString("status", "")
        if (status != "ok") {
            Log.w(TAG, "AcoustID API error: status=$status, error=${root.optString("error")}")
            return null
        }

        val results = root.optJSONArray("results") ?: return null
        if (results.length() == 0) {
            Log.i(TAG, "AcoustID: no matching results")
            return null
        }

        for (i in 0 until results.length()) {
            val result = results.getJSONObject(i)
            val score = result.optDouble("score", 0.0)
            if (score < 0.5) continue

            val recordings = result.optJSONArray("recordings") ?: continue
            if (recordings.length() == 0) continue

            val recording = recordings.getJSONObject(0)
            val recordingId = recording.optString("id", "")
            if (recordingId.isBlank()) continue

            val title = recording.optString("title", "").ifBlank { null }

            var artist: String? = null
            val artists = recording.optJSONArray("artists")
            if (artists != null && artists.length() > 0) {
                artist = artists.getJSONObject(0).optString("name", "").ifBlank { null }
            }

            var album: String? = null
            val releaseGroups = recording.optJSONArray("releasegroups")
            if (releaseGroups != null && releaseGroups.length() > 0) {
                album = releaseGroups.getJSONObject(0).optString("title", "").ifBlank { null }
            }

            if (title != null || artist != null || album != null) {
                Log.i(TAG, "AcoustID match (score=$score): $title / $artist / $album")

                val mbResult = fetchMusicBrainzDetails(recordingId)

                return MusicMetadata(
                    title = title,
                    artist = artist,
                    album = album,
                    year = mbResult?.year,
                    genre = mbResult?.genre,
                    trackNumber = null,
                    albumArtBytes = null,
                    albumArtMime = "image/jpeg"
                )
            }
        }

        return null
    }

    private data class MbDetails(val year: String?, val genre: String?)

    private fun fetchMusicBrainzDetails(recordingId: String): MbDetails? {
        val url = "https://musicbrainz.org/ws/2/recording/$recordingId?fmt=json&inc=releases+artists"
        val json = httpGet(url) ?: return null

        val root = JSONObject(json)

        var year: String? = null
        val releases = root.optJSONArray("releases")
        if (releases != null && releases.length() > 0) {
            val release = releases.getJSONObject(0)
            val date = release.optString("date", "")
            year = date.take(4).ifBlank { null }
        }

        var genre: String? = null
        val tags = root.optJSONArray("tags")
        if (tags != null && tags.length() > 0) {
            for (i in 0 until tags.length()) {
                val tag = tags.getJSONObject(i).optString("name", "")
                if (isMusicGenre(tag)) {
                    genre = tag
                    break
                }
            }
        }

        return MbDetails(year, genre)
    }

    private fun isMusicGenre(tag: String): Boolean {
        val genres = setOf(
            "rock", "pop", "jazz", "blues", "country", "hip hop", "rap", "r&b",
            "soul", "funk", "reggae", "ska", "punk", "metal", "alternative",
            "indie", "electronic", "dance", "house", "techno", "trance",
            "classical", "opera", "folk", "gospel", "latin", "samba", "bossa nova",
            "mpb", "forró", "sertanejo", "axé", "pagode", "funk carioca",
            "brazilian", "pop rock", "rock brasileiro", "eletrônica",
            "instrumental", "acoustic", "lo-fi", "ambient", "new age"
        )
        return tag.lowercase() in genres
    }

    private fun httpGet(urlString: String): String? {
        var conn: HttpURLConnection? = null
        return try {
            conn = URL(urlString).openConnection() as HttpURLConnection
            conn.connectTimeout = TIMEOUT_MS
            conn.readTimeout = TIMEOUT_MS
            conn.requestMethod = "GET"
            conn.setRequestProperty("User-Agent", "MP3Player-Android/1.0 (acoustid-integration)")
            conn.connect()
            if (conn.responseCode != 200) {
                Log.w(TAG, "HTTP ${conn.responseCode} for $urlString")
                null
            } else {
                conn.inputStream.bufferedReader().readText()
            }
        } catch (e: Exception) {
            Log.w(TAG, "HTTP GET error: ${e.message} for $urlString")
            null
        } finally {
            conn?.disconnect()
        }
    }

    private fun httpPost(urlString: String, params: String): String? {
        var conn: HttpURLConnection? = null
        return try {
            conn = URL(urlString).openConnection() as HttpURLConnection
            conn.connectTimeout = TIMEOUT_MS
            conn.readTimeout = TIMEOUT_MS
            conn.requestMethod = "POST"
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
            conn.setRequestProperty("User-Agent", "MP3Player-Android/1.0 (acoustid-integration)")
            conn.connect()
            conn.outputStream.write(params.toByteArray())
            conn.outputStream.flush()
            conn.outputStream.close()
            if (conn.responseCode != 200) {
                Log.w(TAG, "HTTP ${conn.responseCode} for POST $urlString")
                val err = conn.errorStream?.bufferedReader()?.readText() ?: ""
                Log.w(TAG, "Error body: $err")
                null
            } else {
                conn.inputStream.bufferedReader().readText()
            }
        } catch (e: Exception) {
            Log.w(TAG, "HTTP POST error: ${e.message} for $urlString")
            null
        } finally {
            conn?.disconnect()
        }
    }
}
