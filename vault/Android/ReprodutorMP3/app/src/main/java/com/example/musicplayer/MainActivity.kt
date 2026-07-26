package com.example.musicplayer

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.example.musicplayer.data.Track
import com.example.musicplayer.player.MusicPlayerService
import com.example.musicplayer.player.PlayerState
import com.example.musicplayer.ui.MusicPlayerApp
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import android.provider.MediaStore
import android.content.ContentUris

class MainActivity : ComponentActivity() {
    private var musicPlayerService: MusicPlayerService? = null
    private val isBound = mutableStateOf(false)
    private val trackList = mutableStateListOf<Track>()
    private val playerState = mutableStateOf(PlayerState())

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            refreshTrackList()
        }
    }

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            val binder = service as? MusicPlayerService.LocalBinder ?: return
            musicPlayerService = binder.getService()
            isBound.value = true
            lifecycleScope.launch {
                musicPlayerService?.playerState?.collectLatest { state ->
                    playerState.value = state
                }
            }
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            isBound.value = false
            musicPlayerService = null
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        bindMusicService()

        setContent {
            MusicPlayerApp(
                tracks = trackList,
                playerState = playerState.value,
                permissionGranted = checkPermission(),
                onRequestPermission = { requestPermission() },
                onTrackSelected = { track -> musicPlayerService?.playTrack(track) },
                onPlayPause = { musicPlayerService?.togglePlayPause() },
                onSeek = { position -> musicPlayerService?.seekTo(position) },
                onStop = { musicPlayerService?.stopPlayback() },
                onNext = { playNextTrack() },
                onPrevious = { playPreviousTrack() }
            )
        }
    }

    override fun onResume() {
        super.onResume()
        if (checkPermission()) {
            refreshTrackList()
        } else {
            requestPermission()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        if (isBound.value) {
            unbindService(serviceConnection)
            isBound.value = false
        }
    }

    private fun bindMusicService() {
        Intent(this, MusicPlayerService::class.java).also { intent ->
            bindService(intent, serviceConnection, Context.BIND_AUTO_CREATE)
            startService(intent)
        }
    }

    private fun checkPermission(): Boolean {
        val permission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            Manifest.permission.READ_MEDIA_AUDIO
        } else {
            Manifest.permission.READ_EXTERNAL_STORAGE
        }
        return ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED
    }

    private fun requestPermission() {
        val permission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            Manifest.permission.READ_MEDIA_AUDIO
        } else {
            Manifest.permission.READ_EXTERNAL_STORAGE
        }
        permissionLauncher.launch(permission)
    }

    private fun refreshTrackList() {
        lifecycleScope.launch {
            val tracks = loadAudioTracks(this@MainActivity)
            trackList.clear()
            trackList.addAll(tracks)
        }
    }

    private suspend fun loadAudioTracks(context: Context): List<Track> {
        val contentResolver = context.contentResolver
        val uri = MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
        val projection = arrayOf(
            MediaStore.Audio.Media._ID,
            MediaStore.Audio.Media.TITLE,
            MediaStore.Audio.Media.ARTIST,
            MediaStore.Audio.Media.DURATION
        )
        val selection = "${MediaStore.Audio.Media.IS_MUSIC} = 1"
        val sortOrder = "${MediaStore.Audio.Media.TITLE} ASC"

        val tracks = mutableListOf<Track>()
        contentResolver.query(uri, projection, selection, null, sortOrder)?.use { cursor ->
            val idIndex = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
            val titleIndex = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE)
            val artistIndex = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.ARTIST)
            val durationIndex = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.DURATION)

            while (cursor.moveToNext()) {
                val id = cursor.getLong(idIndex)
                val title = cursor.getString(titleIndex) ?: "Unknown title"
                val artist = cursor.getString(artistIndex) ?: "Unknown artist"
                val duration = cursor.getLong(durationIndex)
                val contentUri = ContentUris.withAppendedId(uri, id)

                tracks += Track(id, title, artist, duration, contentUri)
            }
        }
        return tracks
    }

    private fun getCurrentTrackIndex(): Int {
        val currentTrack = playerState.value.currentTrack ?: return -1
        return trackList.indexOfFirst { it.id == currentTrack.id }
    }

    private fun playTrackAt(index: Int) {
        val track = trackList.getOrNull(index) ?: return
        musicPlayerService?.playTrack(track)
    }

    private fun playNextTrack() {
        val nextIndex = getCurrentTrackIndex().takeIf { it >= 0 }?.let { it + 1 } ?: 0
        if (nextIndex < trackList.size) {
            playTrackAt(nextIndex)
        }
    }

    private fun playPreviousTrack() {
        val prevIndex = getCurrentTrackIndex().takeIf { it > 0 }?.let { it - 1 } ?: -1
        if (prevIndex >= 0) {
            playTrackAt(prevIndex)
        }
    }
}
