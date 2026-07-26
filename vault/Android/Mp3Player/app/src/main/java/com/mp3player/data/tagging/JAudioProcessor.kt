package com.mp3player.data.tagging

import com.mp3player.data.model.MusicMetadata
import org.jaudiotagger.audio.AudioFileIO
import org.jaudiotagger.tag.FieldKey
import org.jaudiotagger.tag.images.ArtworkFactory
import java.io.File

class JAudioProcessor : TagProcessor {

    override val name: String get() = "JAudioTagger"

    override fun read(file: File): MusicMetadata? {
        return try {
            val audioFile = AudioFileIO.read(file)
            val tag = audioFile.tag ?: return null

            val artwork = tag.firstArtwork
            val artBytes = artwork?.binaryData
            val artMime = artwork?.mimeType

            MusicMetadata(
                title = tag.getFirst(FieldKey.TITLE).ifBlank { null },
                artist = tag.getFirst(FieldKey.ARTIST).ifBlank { null },
                album = tag.getFirst(FieldKey.ALBUM).ifBlank { null },
                year = tag.getFirst(FieldKey.YEAR).ifBlank { null },
                genre = tag.getFirst(FieldKey.GENRE).ifBlank { null },
                trackNumber = tag.getFirst(FieldKey.TRACK).ifBlank { null },
                albumArtBytes = artBytes,
                albumArtMime = artMime
            )
        } catch (_: Exception) { null }
    }

    override fun write(file: File, metadata: MusicMetadata, backupFile: File?): Boolean {
        return try {
            val audioFile = AudioFileIO.read(file)
            val tag = audioFile.tagOrCreateAndSetDefault

            metadata.title?.let { tag.setField(FieldKey.TITLE, it) }
            metadata.artist?.let { tag.setField(FieldKey.ARTIST, it) }
            metadata.album?.let { tag.setField(FieldKey.ALBUM, it) }
            metadata.year?.let { tag.setField(FieldKey.YEAR, it) }
            metadata.genre?.let { tag.setField(FieldKey.GENRE, it) }
            metadata.trackNumber?.let { tag.setField(FieldKey.TRACK, it) }

            metadata.albumArtBytes?.let { bytes ->
                val artwork = ArtworkFactory.getNew().apply {
                    binaryData = bytes
                    mimeType = metadata.albumArtMime ?: "image/jpeg"
                }
                tag.setField(artwork)
            }

            audioFile.commit()
            true
        } catch (_: Exception) { false }
    }
}
