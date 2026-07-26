package com.example.musicplayer.data

import android.net.Uri

data class Track(
    val id: Long,
    val title: String,
    val artist: String,
    val duration: Long,
    val uri: Uri,
) {
    val durationText: String
        get() {
            val seconds = duration / 1000
            val minutes = seconds / 60
            val remainingSeconds = seconds % 60
            return "%d:%02d".format(minutes, remainingSeconds)
        }
}
