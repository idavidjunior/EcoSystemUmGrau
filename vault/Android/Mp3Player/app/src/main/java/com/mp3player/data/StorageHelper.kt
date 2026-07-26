package com.mp3player.data

import android.content.Context
import android.net.Uri
import android.os.Build
import android.os.ParcelFileDescriptor
import android.provider.MediaStore
import android.util.Log
import com.mp3player.data.model.MusicMetadata
import com.mp3player.data.tagging.FallbackTagProcessor
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream

object StorageHelper {

    private const val TAG = "StorageHelper"
    private val tagProcessor by lazy { FallbackTagProcessor.getInstance() }

    fun writeTagsSafe(
        context: Context,
        songId: Long,
        filePath: String,
        metadata: MusicMetadata
    ): Boolean {
        // Strategy 1: Direct file write (works with MANAGE_EXTERNAL_STORAGE or pre-Android 10)
        try {
            val file = File(filePath)
            if (tagProcessor.safeWriteWithBackup(file, metadata)) {
                Log.i(TAG, "Direct file write succeeded for $filePath")
                updateMediaStore(context, songId, metadata)
                return true
            }
        } catch (e: SecurityException) {
            Log.w(TAG, "Direct file write denied, trying PFD fallback: ${e.message}")
        } catch (e: Exception) {
            Log.w(TAG, "Direct file write failed: ${e.message}")
        }

        // Strategy 2: ParcelFileDescriptor via MediaStore (Android 10+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            try {
                val collection = MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL)
                val uri = Uri.withAppendedPath(collection, songId.toString())

                context.contentResolver.openFileDescriptor(uri, "rw")?.use { pfd ->
                    val tempFile = createTempFileFromPfd(pfd, filePath)
                    if (tempFile != null) {
                        val ok = tagProcessor.safeWriteWithBackup(tempFile, metadata)
                        if (ok) {
                            copyBackToPfd(tempFile, pfd)
                            Log.i(TAG, "PFD-based write succeeded for $filePath")
                            updateMediaStore(context, songId, metadata)
                            tempFile.delete()
                            return true
                        }
                        tempFile.delete()
                    }
                }
            } catch (e: SecurityException) {
                Log.w(TAG, "PFD write denied: ${e.message}")
            } catch (e: Exception) {
                Log.w(TAG, "PFD write failed: ${e.message}")
            }
        }

        Log.e(TAG, "All write strategies failed for $filePath")
        return false
    }

    private fun createTempFileFromPfd(pfd: ParcelFileDescriptor, originalPath: String): File? {
        return try {
            val ext = originalPath.substringAfterLast('.', "mp3")
            val temp = File.createTempFile("tag_edit_", ".$ext")
            FileInputStream(pfd.fileDescriptor).use { input ->
                FileOutputStream(temp).use { output ->
                    input.copyTo(output)
                }
            }
            temp
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create temp file from PFD: ${e.message}")
            null
        }
    }

    private fun copyBackToPfd(tempFile: File, pfd: ParcelFileDescriptor) {
        try {
            FileOutputStream(pfd.fileDescriptor).use { output ->
                tempFile.inputStream().use { input ->
                    input.copyTo(output)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to copy back to PFD: ${e.message}")
        }
    }

    private fun updateMediaStore(context: Context, songId: Long, metadata: MusicMetadata) {
        try {
            val values = android.content.ContentValues().apply {
                metadata.title?.let { put(MediaStore.Audio.Media.TITLE, it) }
                metadata.artist?.let { put(MediaStore.Audio.Media.ARTIST, it) }
                metadata.album?.let { put(MediaStore.Audio.Media.ALBUM, it) }
            }
            if (values.size() > 0) {
                val rows = context.contentResolver.update(
                    MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
                    values,
                    "${MediaStore.Audio.Media._ID} = ?",
                    arrayOf(songId.toString())
                )
                Log.i(TAG, "MediaStore updated: $rows row(s): title=${metadata.title}, artist=${metadata.artist}, album=${metadata.album}")
            }
        } catch (e: Exception) {
            Log.e(TAG, "MediaStore update failed: ${e.message}")
        }
    }
}
