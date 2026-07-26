package com.mp3player.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.mp3player.MusicPlayer
import com.mp3player.RepeatMode
import com.mp3player.ShuffleMode
import com.mp3player.Song
import com.mp3player.data.repository.MusicRepository
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

@OptIn(ExperimentalCoroutinesApi::class)
class PlayerViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = MusicRepository(application)

    private val _currentSong = MutableStateFlow<Song?>(null)
    val currentSong: StateFlow<Song?> = _currentSong.asStateFlow()

    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying.asStateFlow()

    private val _queue = MutableStateFlow<List<Song>>(emptyList())
    val queue: StateFlow<List<Song>> = _queue.asStateFlow()

    private val _repeatMode = MutableStateFlow(RepeatMode.ALL)
    val repeatMode: StateFlow<RepeatMode> = _repeatMode.asStateFlow()

    private val _shuffleMode = MutableStateFlow(ShuffleMode.OFF)
    val shuffleMode: StateFlow<ShuffleMode> = _shuffleMode.asStateFlow()

    private val _currentPosition = MutableStateFlow(0)
    val currentPosition: StateFlow<Int> = _currentPosition.asStateFlow()

    private val _duration = MutableStateFlow(0)
    val duration: StateFlow<Int> = _duration.asStateFlow()

    private val _isFavorite = MutableStateFlow(false)
    val isFavorite: StateFlow<Boolean> = _isFavorite.asStateFlow()

    private val _favorites = repository.getAllFavorites()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
    val favorites: StateFlow<List<com.mp3player.data.entity.FavoriteEntity>> = _favorites

    val playlists = repository.getAllPlaylists()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    private var songChangedListener: ((Song) -> Unit)? = null
    private var playStateListener: ((Boolean) -> Unit)? = null

    init {
        viewModelScope.launch {
            _currentSong
                .filterNotNull()
                .flatMapLatest { repository.isFavorite(it.path) }
                .collect { fav -> _isFavorite.value = fav }
        }
    }

    fun linkToMusicPlayer(musicPlayer: MusicPlayer) {
        songChangedListener?.let { musicPlayer.removeSongChangedListener(it) }
        playStateListener?.let { musicPlayer.removePlayStateListener(it) }
        songChangedListener = { song ->
            _currentSong.value = song
            _duration.value = musicPlayer.getDuration()
            viewModelScope.launch {
                musicPlayer.getDuration().let { _duration.value = it }
            }
        }
        playStateListener = { playing ->
            _isPlaying.value = playing
        }
        musicPlayer.addSongChangedListener(songChangedListener!!)
        musicPlayer.addPlayStateListener(playStateListener!!)
        _repeatMode.value = musicPlayer.repeatMode
        _shuffleMode.value = musicPlayer.shuffleMode
    }

    fun updateQueue(queue: List<Song>) {
        _queue.value = queue
    }

    fun updateCurrentPosition(position: Int) {
        _currentPosition.value = position
    }

    fun toggleFavorite(song: Song) {
        viewModelScope.launch {
            repository.toggleFavorite(song)
        }
    }

    fun createPlaylist(name: String, onCreated: (Long) -> Unit = {}) {
        viewModelScope.launch {
            val id = repository.createPlaylist(name)
            onCreated(id)
        }
    }

    fun deletePlaylist(id: Long) {
        viewModelScope.launch {
            repository.deletePlaylist(id)
        }
    }

    fun addSongToPlaylist(playlistId: Long, song: Song) {
        viewModelScope.launch {
            repository.getPlaylistSongs(playlistId).first().let { current ->
                repository.addSongToPlaylist(playlistId, song, current.size)
            }
        }
    }
}
