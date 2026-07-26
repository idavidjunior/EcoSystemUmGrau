package com.mp3player.data

import android.app.AlertDialog
import android.content.ContentValues
import android.content.Context
import android.media.MediaMetadataRetriever
import android.os.Build
import android.provider.MediaStore
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.Toast
import com.mp3player.Song
import com.mp3player.data.model.MusicMetadata
import com.mp3player.data.tagging.FallbackTagProcessor
import java.io.File

object TagEditor {

    private val tagProcessor by lazy { FallbackTagProcessor.getInstance() }

    fun readEmbeddedTags(path: String): MusicMetadata? {
        return tagProcessor.read(File(path))
    }

    fun writeTags(path: String, metadata: MusicMetadata): Boolean {
        return tagProcessor.safeWriteWithBackup(File(path), metadata)
    }

    fun updateMediaStore(context: Context, songId: Long, title: String, artist: String, album: String) {
        try {
            val values = ContentValues().apply {
                put(MediaStore.Audio.Media.TITLE, title)
                put(MediaStore.Audio.Media.ARTIST, artist)
                put(MediaStore.Audio.Media.ALBUM, album)
            }
            context.contentResolver.update(
                MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
                values,
                "${MediaStore.Audio.Media._ID} = ?",
                arrayOf(songId.toString())
            )
        } catch (e: SecurityException) {
            android.util.Log.e("TagEditor", "MediaStore update denied: ${e.message}")
        }
    }

    private fun getMediaStoreSongsByAlbum(context: Context, albumName: String): List<String> {
        if (albumName.isBlank()) return emptyList()
        val paths = mutableListOf<String>()
        try {
            val collection = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q)
                MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL)
            else
                MediaStore.Audio.Media.EXTERNAL_CONTENT_URI

            val projection = arrayOf(MediaStore.Audio.Media.DATA)
            val selection = "${MediaStore.Audio.Media.ALBUM} = ? AND ${MediaStore.Audio.Media.IS_MUSIC} != 0"
            val args = arrayOf(albumName)

            context.contentResolver.query(collection, projection, selection, args, null)?.use { c ->
                while (c.moveToNext()) {
                    val path = c.getString(0) ?: continue
                    paths.add(path)
                }
            }
        } catch (_: Exception) {}
        return paths
    }

    private fun getMediaStoreSongsByArtist(context: Context, artistName: String): List<String> {
        if (artistName.isBlank() || artistName == "Desconhecido" || artistName == "<unknown>") return emptyList()
        val paths = mutableListOf<String>()
        try {
            val collection = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q)
                MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL)
            else
                MediaStore.Audio.Media.EXTERNAL_CONTENT_URI

            val projection = arrayOf(MediaStore.Audio.Media.DATA)
            val selection = "${MediaStore.Audio.Media.ARTIST} = ? AND ${MediaStore.Audio.Media.IS_MUSIC} != 0"
            val args = arrayOf(artistName)

            context.contentResolver.query(collection, projection, selection, args, null)?.use { c ->
                while (c.moveToNext()) {
                    val path = c.getString(0) ?: continue
                    paths.add(path)
                }
            }
        } catch (_: Exception) {}
        return paths
    }

    private fun readEmbeddedWithRetriever(path: String): MusicMetadata? {
        return try {
            MediaMetadataRetriever().use { r ->
                r.setDataSource(path)
                val title = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_TITLE)
                val artist = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ARTIST)
                val album = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ALBUM)
                val art = r.embeddedPicture
                MusicMetadata(
                    title = title?.ifBlank { null },
                    artist = artist?.ifBlank { null },
                    album = album?.ifBlank { null },
                    albumArtBytes = art,
                    albumArtMime = when {
                        art != null && art.size > 2 && art[0] == 0xFF.toByte() && art[1] == 0xD8.toByte() -> "image/jpeg"
                        art != null && art.size > 8 && art[0] == 0x89.toByte() && art[1] == 0x50.toByte() -> "image/png"
                        else -> "image/jpeg"
                    }
                )
            }
        } catch (_: Exception) { null }
    }

    private fun String?.isUsable(): Boolean {
        return this != null && !isBlank() && this != "<unknown>" && this != "Desconhecido"
    }

    private fun mergeMetadata(others: List<MusicMetadata>): MusicMetadata {
        var title: String? = null
        var artist: String? = null
        var album: String? = null
        var artBytes: ByteArray? = null
        var artMime = "image/jpeg"
        for (m in others) {
            if (title == null && m.title.isUsable()) title = m.title
            if (artist == null && m.artist.isUsable()) artist = m.artist
            if (album == null && m.album.isUsable()) album = m.album
            if (artBytes == null && m.albumArtBytes != null) {
                artBytes = m.albumArtBytes
                artMime = m.albumArtMime ?: "image/jpeg"
            }
            if (title != null && artist != null && album != null && artBytes != null) break
        }
        return MusicMetadata(title, artist, album, null, null, null, artBytes, artMime)
    }

    private fun findAlbumInfo(songPath: String, songAlbum: String, songArtist: String, context: Context): MusicMetadata {
        val selfMeta = readEmbeddedWithRetriever(songPath)

        // Collect paths: first by album, then by artist
        val selfAlbum = selfMeta?.album
        val albumPaths = getMediaStoreSongsByAlbum(context, songAlbum)
        val paths = if (selfAlbum.isUsable() && selfAlbum != songAlbum) {
            (albumPaths + getMediaStoreSongsByAlbum(context, selfAlbum!!)).distinct()
        } else {
            albumPaths
        }

        val allCandidates = mutableListOf<MusicMetadata>()
        if (selfMeta != null) allCandidates.add(selfMeta)

        val visited = mutableSetOf(songPath)
        for (p in paths) {
            if (!visited.add(p)) continue
            readEmbeddedWithRetriever(p)?.let { allCandidates.add(it) }
        }

        // If no results from album search, try artist search
        if (allCandidates.size <= 1) {
            val artistPaths = getMediaStoreSongsByArtist(context, songArtist)
            for (p in artistPaths) {
                if (!visited.add(p)) continue
                readEmbeddedWithRetriever(p)?.let { allCandidates.add(it) }
            }
        }

        val merged = mergeMetadata(allCandidates)

        // If merged has nothing, fall back to folder cover only
        if (merged.albumArtBytes == null) {
            val folder = AlbumArtProvider.findCoverBytes(songPath)
            if (folder != null) {
                return merged.copy(
                    albumArtBytes = folder,
                    albumArtMime = when {
                        folder.size > 2 && folder[0] == 0xFF.toByte() && folder[1] == 0xD8.toByte() -> "image/jpeg"
                        folder.size > 8 && folder[0] == 0x89.toByte() && folder[1] == 0x50.toByte() -> "image/png"
                        else -> "image/jpeg"
                    }
                )
            }
        }

        return merged
    }

    fun showEditDialog(context: Context, song: Song, onSaved: () -> Unit) {
        val layout = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 20, 40, 20)
        }

        val etTitle = EditText(context).apply { setText(song.title); hint = "Título" }
        val etArtist = EditText(context).apply { setText(song.artist); hint = "Artista" }
        val etAlbum = EditText(context).apply { setText(song.album); hint = "Álbum" }

        layout.addView(etTitle)
        layout.addView(etArtist)
        layout.addView(etAlbum)

        val previewArt = ImageView(context).apply {
            layoutParams = LinearLayout.LayoutParams(120, 120).apply { setMargins(0, 16, 0, 8) }
            scaleType = ImageView.ScaleType.CENTER_CROP
            setBackgroundColor(0xFF2A2A2A.toInt())
        }
        layout.addView(previewArt)

        var selectedArtBytes: ByteArray? = null
        var selectedMime = "image/jpeg"

        fun setPreviewArt(bytes: ByteArray?, mime: String) {
            if (bytes != null) {
                selectedArtBytes = bytes
                selectedMime = mime
                val bmp = android.graphics.BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                if (bmp != null) {
                    previewArt.setImageBitmap(bmp)
                }
            }
        }

        fun loadArtPreview() {
            val albumName = etAlbum.text.toString().trim().ifBlank { song.album }
            val artistName = etArtist.text.toString().trim().ifBlank { song.artist }
            // Reuse findAlbumInfo to do a focused art search
            val info = findAlbumInfo(song.path, albumName, artistName, context)
            if (info.albumArtBytes != null) {
                setPreviewArt(info.albumArtBytes, info.albumArtMime ?: "image/jpeg")
                Toast.makeText(context, "Capa encontrada (${info.albumArtBytes.size / 1024} KB)", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(context, "Nenhuma capa encontrada", Toast.LENGTH_SHORT).show()
            }
        }

        // Auto-search: find best metadata from other songs in same album
        val searchAlbum = song.album
        val searchArtist = song.artist
        if (searchAlbum.isNotBlank() || (searchArtist.isNotBlank() && searchArtist != "Desconhecido" && searchArtist != "<unknown>")) {
            val info = findAlbumInfo(song.path, searchAlbum, searchArtist, context)
            var changed = false
            if (info.title.isUsable() && info.title != song.title) {
                etTitle.setText(info.title)
                changed = true
            }
            if (info.artist.isUsable() && info.artist != song.artist) {
                etArtist.setText(info.artist)
                changed = true
            }
            if (info.album.isUsable() && info.album != song.album) {
                etAlbum.setText(info.album)
                changed = true
            }
            if (info.albumArtBytes != null) {
                setPreviewArt(info.albumArtBytes, info.albumArtMime ?: "image/jpeg")
            } else {
                // Try folder cover as last resort
                val folder = AlbumArtProvider.findCoverBytes(song.path)
                if (folder != null) {
                    setPreviewArt(folder, when {
                        folder.size > 2 && folder[0] == 0xFF.toByte() && folder[1] == 0xD8.toByte() -> "image/jpeg"
                        folder.size > 8 && folder[0] == 0x89.toByte() && folder[1] == 0x50.toByte() -> "image/png"
                        else -> "image/jpeg"
                    })
                }
            }
            if (changed) {
                Toast.makeText(context, "Metadados corrigidos automaticamente", Toast.LENGTH_SHORT).show()
            }
        }

        AlertDialog.Builder(context)
            .setTitle("Editar metadados")
            .setView(layout)
            .setPositiveButton("Salvar") { _, _ ->
                val newTitle = etTitle.text.toString().trim()
                val newArtist = etArtist.text.toString().trim()
                val newAlbum = etAlbum.text.toString().trim()

                val metadata = MusicMetadata(
                    title = newTitle.ifBlank { null },
                    artist = newArtist.ifBlank { null },
                    album = newAlbum.ifBlank { null },
                    albumArtBytes = selectedArtBytes,
                    albumArtMime = selectedMime
                )
                val fileOk = writeTags(song.path, metadata)
                if (fileOk) {
                    updateMediaStore(
                        context, song.id,
                        metadata.title ?: song.title,
                        metadata.artist ?: song.artist,
                        metadata.album ?: song.album
                    )
                    Toast.makeText(context, "Metadados salvos com sucesso!", Toast.LENGTH_SHORT).show()
                    onSaved()
                } else {
                    Toast.makeText(context, "Erro ao salvar metadados no arquivo. Verifique as permissões.", Toast.LENGTH_LONG).show()
                }
            }
            .setNeutralButton("Buscar capa") { _, _ -> loadArtPreview() }
            .setNegativeButton("Cancelar", null)
            .show()
    }

}
