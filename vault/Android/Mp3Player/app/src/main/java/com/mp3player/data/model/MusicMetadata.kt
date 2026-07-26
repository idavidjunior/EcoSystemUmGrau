package com.mp3player.data.model

data class MusicMetadata(
    val title: String? = null,
    val artist: String? = null,
    val album: String? = null,
    val year: String? = null,
    val genre: String? = null,
    val trackNumber: String? = null,
    val albumArtBytes: ByteArray? = null,
    val albumArtMime: String? = null
) {
    val isComplete: Boolean get() = title != null && artist != null && album != null

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is MusicMetadata) return false
        return title == other.title &&
                artist == other.artist &&
                album == other.album &&
                year == other.year &&
                genre == other.genre &&
                trackNumber == other.trackNumber &&
                albumArtBytes.contentEquals(other.albumArtBytes ?: byteArrayOf()) &&
                albumArtMime == other.albumArtMime
    }

    override fun hashCode(): Int {
        var result = title.hashCode()
        result = 31 * result + artist.hashCode()
        result = 31 * result + album.hashCode()
        return result
    }
}
