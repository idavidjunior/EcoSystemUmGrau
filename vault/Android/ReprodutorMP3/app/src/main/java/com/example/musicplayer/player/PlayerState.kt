package com.example.musicplayer.player

import com.example.musicplayer.data.Track

data class PlayerState(
    val currentTrack: Track? = null,
    val isPlaying: Boolean = false,
    val position: Long = 0L,
    val duration: Long = 0L,
)
