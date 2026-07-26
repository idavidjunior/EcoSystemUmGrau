package com.mp3player.data.tagging

import android.util.Log
import com.mp3player.data.model.MusicMetadata
import java.io.File
import java.io.RandomAccessFile
import java.util.UUID

class FallbackTagProcessor(
    private val processors: List<TagProcessor> = listOf(
        JAudioProcessor(),
        Mp3agicProcessor()
    )
) : TagProcessor {

    companion object {
        private const val TAG = "FallbackTagProcessor"
        private const val MAX_RETRY_SAME_PROCESSOR = 1

        @Volatile
        private var instance: FallbackTagProcessor? = null

        fun getInstance(): FallbackTagProcessor {
            return instance ?: synchronized(this) {
                instance ?: FallbackTagProcessor().also { instance = it }
            }
        }
    }

    override val name: String get() = "FallbackChain"

    override fun read(file: File): MusicMetadata? {
        var best: MusicMetadata? = null
        var bestScore = -1
        for (processor in processors) {
            try {
                val result = processor.read(file)
                if (result != null) {
                    val score = listOfNotNull(result.title, result.artist, result.album).size
                    if (score > bestScore) {
                        best = result
                        bestScore = score
                        logSuccess(processor.name, "read", file)
                    }
                    if (result.isComplete) {
                        return result
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "[${processor.name}] read failed for ${file.name}: ${e.message}")
            }
        }
        if (best != null) {
            Log.w(TAG, "Best partial metadata (score=$bestScore/3) for ${file.name}")
            return best
        }
        Log.w(TAG, "All processors failed to read metadata for ${file.name}")
        return null
    }

    override fun write(file: File, metadata: MusicMetadata, backupFile: File?): Boolean {
        for (processor in processors) {
            try {
                val result = processor.write(file, metadata, backupFile)
                if (result) {
                    logSuccess(processor.name, "write", file)
                    return true
                }
            } catch (e: Exception) {
                Log.e(TAG, "[${processor.name}] write failed for ${file.name}: ${e.message}")
            }
        }
        Log.e(TAG, "All processors failed to write metadata for ${file.name}")
        return false
    }

    fun safeWriteWithBackup(file: File, metadata: MusicMetadata): Boolean {
        val backup = createBackup(file)
        try {
            val result = write(file, metadata, backup)
            if (!result) restoreBackup(file, backup)
            return result
        } catch (e: Exception) {
            restoreBackup(file, backup)
            Log.e(TAG, "Safe write failed for ${file.name}: ${e.message}")
            return false
        } finally {
            backup?.delete()
        }
    }

    private fun createBackup(file: File): File? {
        return try {
            if (!file.exists()) return null
            val backup = File(file.parentFile, ".${file.name}.${UUID.randomUUID()}.bak")
            file.copyTo(backup, overwrite = true)
            backup
        } catch (e: Exception) {
            Log.w(TAG, "Failed to create backup for ${file.name}: ${e.message}")
            null
        }
    }

    private fun restoreBackup(file: File, backup: File?) {
        if (backup == null || !backup.exists()) return
        try {
            backup.copyTo(file, overwrite = true)
            Log.i(TAG, "Restored backup for ${file.name}")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to restore backup for ${file.name}: ${e.message}")
        }
    }

    private fun logSuccess(processor: String, operation: String, file: File) {
        Log.i(TAG, "[$processor] $operation succeeded for ${file.name}")
    }
}
