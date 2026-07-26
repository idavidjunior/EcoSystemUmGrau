package com.mp3player.data.tagging

import com.mpatric.mp3agic.ID3v23Tag
import com.mpatric.mp3agic.Mp3File
import com.mp3player.data.model.MusicMetadata
import java.io.File

class Mp3agicProcessor : TagProcessor {

    override val name: String get() = "mp3agic"

    override fun read(file: File): MusicMetadata? {
        return try {
            val mp3 = Mp3File(file.absolutePath)
            if (!mp3.hasId3v2Tag()) return null

            val tag = mp3.id3v2Tag
            MusicMetadata(
                title = tag.title?.ifBlank { null },
                artist = tag.artist?.ifBlank { null },
                album = tag.album?.ifBlank { null },
                year = tag.year?.ifBlank { null },
                genre = tag.genreDescription?.ifBlank { null },
                trackNumber = tag.track?.ifBlank { null },
                albumArtBytes = tag.albumImage,
                albumArtMime = tag.albumImageMimeType
            )
        } catch (_: Exception) { null }
    }

    override fun write(file: File, metadata: MusicMetadata, backupFile: File?): Boolean {
        return try {
            val mp3 = Mp3File(file.absolutePath)
            val tag = if (mp3.hasId3v2Tag()) mp3.id3v2Tag else ID3v23Tag()

            metadata.title?.let { tag.setTitle(it) }
            metadata.artist?.let { tag.setArtist(it) }
            metadata.album?.let { tag.setAlbum(it) }
            metadata.year?.let { tag.setYear(it) }
            metadata.genre?.let { tag.setGenreDescription(it) }
            metadata.trackNumber?.let { tag.setTrack(it) }
            metadata.albumArtBytes?.let { bytes ->
                tag.setAlbumImage(bytes, metadata.albumArtMime ?: "image/jpeg")
            }

            mp3.removeId3v2Tag()
            mp3.setId3v2Tag(tag)
            mp3.save(file.absolutePath)
            true
        } catch (_: Exception) { false }
    }
}
