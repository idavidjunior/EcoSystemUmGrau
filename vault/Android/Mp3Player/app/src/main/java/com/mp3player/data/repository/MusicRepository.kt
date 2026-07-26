package com.mp3player.data.repository

import android.content.Context
import com.mp3player.Song
import com.mp3player.data.AppDatabase
import com.mp3player.data.entity.FavoriteEntity
import com.mp3player.data.entity.PlaylistEntity
import com.mp3player.data.entity.PlaylistSongEntity
import kotlinx.coroutines.flow.Flow

class MusicRepository(private val context: Context) {

    private val db = AppDatabase.getInstance(context)
    private val favoriteDao = db.favoriteDao()
    private val playlistDao = db.playlistDao()

    // Favorites
    fun getAllFavorites(): Flow<List<FavoriteEntity>> = favoriteDao.getAllFavorites()

    fun isFavorite(songPath: String): Flow<Boolean> = favoriteDao.isFavorite(songPath)

    suspend fun isFavoriteSync(songPath: String): Boolean = favoriteDao.isFavoriteSync(songPath)

    suspend fun toggleFavorite(song: Song) {
        if (favoriteDao.isFavoriteSync(song.path)) {
            favoriteDao.removeFavoriteByPath(song.path)
        } else {
            favoriteDao.addFavorite(
                FavoriteEntity(
                    songPath = song.path,
                    title = song.title,
                    artist = song.artist,
                    album = song.album,
                    duration = song.duration
                )
            )
        }
    }

    suspend fun addFavorite(song: Song) {
        favoriteDao.addFavorite(
            FavoriteEntity(
                songPath = song.path,
                title = song.title,
                artist = song.artist,
                album = song.album,
                duration = song.duration
            )
        )
    }

    suspend fun removeFavorite(songPath: String) = favoriteDao.removeFavoriteByPath(songPath)

    fun getFavoriteCount(): Flow<Int> = favoriteDao.getFavoriteCount()

    // Playlists
    fun getAllPlaylists(): Flow<List<PlaylistEntity>> = playlistDao.getAllPlaylists()

    suspend fun createPlaylist(name: String): Long {
        return playlistDao.createPlaylist(PlaylistEntity(name = name))
    }

    suspend fun deletePlaylist(id: Long) = playlistDao.deletePlaylistById(id)

    fun getPlaylistSongs(playlistId: Long): Flow<List<PlaylistSongEntity>> =
        playlistDao.getPlaylistSongs(playlistId)

    suspend fun addSongToPlaylist(playlistId: Long, song: Song, position: Int) {
        playlistDao.addSongToPlaylist(
            PlaylistSongEntity(
                playlistId = playlistId,
                songPath = song.path,
                position = position,
                title = song.title,
                artist = song.artist,
                album = song.album,
                duration = song.duration
            )
        )
        playlistDao.updateSongCount(playlistId)
    }

    suspend fun removeSongFromPlaylist(playlistId: Long, songPath: String) {
        playlistDao.removeSongFromPlaylist(playlistId, songPath)
        playlistDao.updateSongCount(playlistId)
    }

    suspend fun clearPlaylist(playlistId: Long) {
        playlistDao.clearPlaylist(playlistId)
        playlistDao.updateSongCount(playlistId)
    }
}
