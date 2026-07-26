package com.mp3player.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import android.util.LruCache
import java.io.File
import java.io.FileOutputStream

object AlbumArtProvider {

    private val memoryCache = object : LruCache<String, Bitmap>(50 * 1024 * 1024) {
        override fun sizeOf(key: String, value: Bitmap): Int = value.byteCount
    }

    private val cacheDir: String by lazy {
        "${android.os.Environment.getExternalStorageDirectory().absolutePath}/.mp3player_cache"
    }

    fun getAlbumArt(path: String, context: Context? = null): Bitmap? {
        memoryCache.get(path)?.let { return it }

        val fromFile = loadFromFile(path)
        if (fromFile != null) {
            memoryCache.put(path, fromFile)
            return fromFile
        }

        val fromEmbedded = loadEmbedded(path)
        if (fromEmbedded != null) {
            memoryCache.put(path, fromEmbedded)
            saveToCache(path, fromEmbedded)
            return fromEmbedded
        }

        if (context != null) {
            val fromFolder = loadFromFolder(path, context)
            if (fromFolder != null) {
                memoryCache.put(path, fromFolder)
                saveToCache(path, fromFolder)
                return fromFolder
            }
        }

        return null
    }

    private fun loadEmbedded(path: String): Bitmap? {
        return try {
            MediaMetadataRetriever().use { r ->
                r.setDataSource(path)
                val data = r.embeddedPicture
                if (data != null) BitmapFactory.decodeByteArray(data, 0, data.size) else null
            }
        } catch (_: Exception) { null }
    }

    private fun loadFromFile(path: String): Bitmap? {
        return try {
            val cacheFile = File(cacheDir, "${path.hashCode()}.jpg")
            if (cacheFile.exists()) {
                BitmapFactory.decodeFile(cacheFile.absolutePath)
            } else null
        } catch (_: Exception) { null }
    }

    private fun saveToCache(path: String, bmp: Bitmap) {
        try {
            val dir = File(cacheDir)
            if (!dir.exists()) dir.mkdirs()
            val cacheFile = File(dir, "${path.hashCode()}.jpg")
            if (!cacheFile.exists()) {
                FileOutputStream(cacheFile).use { out ->
                    bmp.compress(Bitmap.CompressFormat.JPEG, 85, out)
                }
            }
        } catch (_: Exception) {}
    }

    private fun loadFromFolder(path: String, context: Context): Bitmap? {
        return try {
            val file = File(path)
            val folder = file.parentFile ?: return null

            val imageNames = listOf("folder.jpg", "cover.jpg", "album.jpg", "Folder.jpg", "Cover.jpg", "Album.jpg", "front.jpg", "Front.jpg")
            for (name in imageNames) {
                val imgFile = File(folder, name)
                if (imgFile.exists()) {
                    val bmp = BitmapFactory.decodeFile(imgFile.absolutePath)
                    if (bmp != null) return bmp
                }
            }

            val jpgs = folder.listFiles { f -> f.extension.lowercase() in listOf("jpg", "jpeg", "png") }
            if (jpgs != null) {
                for (img in jpgs) {
                    val bmp = BitmapFactory.decodeFile(img.absolutePath)
                    if (bmp != null) return bmp
                }
            }

            null
        } catch (_: Exception) { null }
    }

    fun clearCache() {
        memoryCache.evictAll()
        try {
            val dir = File(cacheDir)
            if (dir.exists()) dir.deleteRecursively()
        } catch (_: Exception) {}
    }

    fun findCoverBytes(path: String): ByteArray? {
        return try {
            val file = File(path)
            val folder = file.parentFile ?: return null
            val imageNames = listOf("folder.jpg", "cover.jpg", "album.jpg", "Folder.jpg", "Cover.jpg", "Album.jpg", "front.jpg", "Front.jpg")
            for (name in imageNames) {
                val imgFile = File(folder, name)
                if (imgFile.exists()) return imgFile.readBytes()
            }
            val jpgs = folder.listFiles { f -> f.extension.lowercase() in listOf("jpg", "jpeg", "png") }
            if (jpgs != null) {
                for (img in jpgs) {
                    if (img.exists()) return img.readBytes()
                }
            }
            null
        } catch (_: Exception) { null }
    }
}
