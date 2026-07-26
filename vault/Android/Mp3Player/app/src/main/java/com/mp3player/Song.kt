package com.mp3player

data class Song(
    val id: Long,
    val title: String,
    val artist: String,
    val album: String,
    val duration: Long,
    val path: String,
    val dateAdded: Long = 0L
) {
    val folder: String
        get() {
            val idx = path.lastIndexOf('/')
            return if (idx >= 0) path.substring(0, idx) else "/"
        }

    val fileName: String
        get() {
            val idx = path.lastIndexOf('/')
            return if (idx >= 0) path.substring(idx + 1) else path
        }
}
