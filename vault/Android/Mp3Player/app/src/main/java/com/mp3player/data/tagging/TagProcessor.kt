package com.mp3player.data.tagging

import com.mp3player.data.model.MusicMetadata
import java.io.File

interface TagProcessor {
    val name: String

    fun read(file: File): MusicMetadata?

    fun write(file: File, metadata: MusicMetadata, backupFile: File?): Boolean
}
