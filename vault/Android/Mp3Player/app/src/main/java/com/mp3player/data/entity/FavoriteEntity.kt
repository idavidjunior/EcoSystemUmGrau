package com.mp3player.data.entity

import androidx.room.Entity
import androidx.room.Index

@Entity(
    tableName = "favorites",
    primaryKeys = ["songPath"],
    indices = [Index(value = ["songPath"], unique = true)]
)
data class FavoriteEntity(
    val songPath: String,
    val title: String,
    val artist: String,
    val album: String,
    val duration: Long,
    val addedAt: Long = System.currentTimeMillis()
)
