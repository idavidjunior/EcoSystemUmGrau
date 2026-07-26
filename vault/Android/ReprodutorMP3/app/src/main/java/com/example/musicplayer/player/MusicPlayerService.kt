package com.example.musicplayer.player

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Binder
import android.os.Build
import android.os.IBinder
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerNotificationManager
import com.example.musicplayer.MainActivity
import com.example.musicplayer.R
import com.example.musicplayer.data.Track
import com.example.musicplayer.player.PlayerState
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

private const val NOTIFICATION_CHANNEL_ID = "music_player_channel"
private const val NOTIFICATION_ID = 1297
private const val SERVICE_TAG = "MusicPlayerService"

class MusicPlayerService : Service() {
    private val binder = LocalBinder()
    private lateinit var player: ExoPlayer
    private lateinit var playerNotificationManager: PlayerNotificationManager
    private lateinit var notificationManager: NotificationManager
    private val _playerState = MutableStateFlow(PlayerState())
    val playerState: StateFlow<PlayerState> = _playerState
    private val serviceScope = CoroutineScope(Dispatchers.Default)
    private var progressJob: Job? = null

    override fun onCreate() {
        super.onCreate()
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        createNotificationChannel()

        player = ExoPlayer.Builder(this).build().apply {
            addListener(object : Player.Listener {
                override fun onIsPlayingChanged(isPlaying: Boolean) {
                    updateState(isPlaying = isPlaying)
                    if (isPlaying) startProgressUpdates() else stopProgressUpdates()
                }

                override fun onMediaItemTransition(mediaItem: MediaItem?, reason: Int) {
                    updateState()
                }

                override fun onPlaybackStateChanged(playbackState: Int) {
                    updateState()
                }
            })
        }

        playerNotificationManager = PlayerNotificationManager.Builder(this, NOTIFICATION_ID, NOTIFICATION_CHANNEL_ID)
            .setMediaDescriptionAdapter(NotificationDescriptionAdapter())
            .build().apply {
                setPlayer(player)
            }
    }

    override fun onBind(intent: Intent): IBinder = binder

    override fun onUnbind(intent: Intent?): Boolean {
        stopForeground(false)
        return true
    }

    override fun onDestroy() {
        stopProgressUpdates()
        player.release()
        playerNotificationManager.setPlayer(null)
        serviceScope.cancel()
        super.onDestroy()
    }

    fun playTrack(track: Track) {
        val mediaItem = MediaItem.fromUri(track.uri)
        player.setMediaItem(mediaItem)
        player.prepare()
        player.play()
        updateState(currentTrack = track)
        startProgressUpdates()
    }

    fun togglePlayPause() {
        if (player.isPlaying) pausePlayback() else resumePlayback()
    }

    fun pausePlayback() {
        player.pause()
        updateState(isPlaying = false)
    }

    fun resumePlayback() {
        if (player.currentMediaItem != null) {
            player.play()
            updateState(isPlaying = true)
        }
    }

    fun seekTo(positionMs: Long) {
        player.seekTo(positionMs)
        updateState(position = positionMs)
    }

    fun stopPlayback() {
        player.stop()
        updateState(isPlaying = false, position = 0)
        stopForeground(false)
    }

    private fun updateState(
        currentTrack: Track? = _playerState.value.currentTrack,
        isPlaying: Boolean = player.isPlaying,
        position: Long = player.currentPosition,
        duration: Long = player.duration.coerceAtLeast(0L)
    ) {
        _playerState.value = PlayerState(
            currentTrack = currentTrack,
            isPlaying = isPlaying,
            position = position,
            duration = duration
        )
    }

    private fun startProgressUpdates() {
        if (progressJob?.isActive == true) return
        progressJob = serviceScope.launch {
            while (true) {
                delay(500L)
                updateState()
            }
        }
    }

    private fun stopProgressUpdates() {
        progressJob?.cancel()
        progressJob = null
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                getString(com.example.musicplayer.R.string.notification_channel_name),
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = getString(com.example.musicplayer.R.string.notification_channel_description)
            }
            notificationManager.createNotificationChannel(channel)
        }
    }

    inner class LocalBinder : Binder() {
        fun getService(): MusicPlayerService = this@MusicPlayerService
    }

    private inner class NotificationDescriptionAdapter : PlayerNotificationManager.MediaDescriptionAdapter {
        override fun getCurrentContentTitle(player: Player): CharSequence {
            return _playerState.value.currentTrack?.title ?: getString(com.example.musicplayer.R.string.app_name)
        }

        override fun createCurrentContentIntent(player: Player): PendingIntent? {
            return PendingIntent.getActivity(
                this@MusicPlayerService,
                0,
                Intent(this@MusicPlayerService, MainActivity::class.java),
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            )
        }

        override fun getCurrentContentText(player: Player): CharSequence? {
            return _playerState.value.currentTrack?.artist
        }

        override fun getCurrentLargeIcon(player: Player, callback: PlayerNotificationManager.BitmapCallback): android.graphics.Bitmap? {
            return null
        }
    }
}
