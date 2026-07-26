package com.mp3player

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.AudioManager
import android.media.MediaMetadataRetriever
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.support.v4.media.MediaMetadataCompat
import android.support.v4.media.session.MediaSessionCompat
import android.support.v4.media.session.PlaybackStateCompat
import androidx.core.app.NotificationCompat
import androidx.media.app.NotificationCompat as MediaNotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class PlayerService : Service() {

    private val binder = LocalBinder()
    lateinit var musicPlayer: MusicPlayer
        private set
    private var mediaSession: MediaSessionCompat? = null
    private var noisyReceiver: NoisyAudioReceiver? = null
    @Volatile private var cachedAlbumArt: Bitmap? = null
    private var isForeground = false

    inner class LocalBinder : Binder() {
        fun getService(): PlayerService = this@PlayerService
    }

    override fun onCreate() {
        super.onCreate()
        android.util.Log.d(TAG, "=== SERVICE onCreate ===")
        musicPlayer = MusicPlayer(this)
        createNotificationChannel()
        setupMediaSession()

        musicPlayer.addSongChangedListener { song ->
            android.util.Log.d(TAG, "Song changed to: ${song.title}")
            CoroutineScope(Dispatchers.IO).launch {
                cachedAlbumArt = loadAlbumArt(song.path)
                updateNotification(song)
            }
            updateMediaSession(song)
        }
        musicPlayer.addPlayStateListener { playing ->
            android.util.Log.d(TAG, "Play state: $playing")
            updateNotification(musicPlayer.currentSong)
            updatePlaybackState(playing)
            Intent(ACTION_PLAY_STATE_CHANGED).apply {
                putExtra("is_playing", playing)
                sendBroadcast(this)
            }
        }

        registerNoisyReceiver()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action
        android.util.Log.d(TAG, "=== onStartCommand action=$action flags=$flags startId=$startId isForeground=$isForeground ===")
        if (action != null) {
            android.util.Log.d(TAG, "Handling action: $action")
            handleAction(action)
        }
        if (!isForeground) {
            android.util.Log.d(TAG, "startForeground() currentSong=${musicPlayer.currentSong?.title}")
            val notification = buildNotification(musicPlayer.currentSong)
            startForeground(NOTIFICATION_ID, notification)
            isForeground = true
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onDestroy() {
        android.util.Log.d(TAG, "=== SERVICE onDestroy ===")
        unregisterNoisyReceiver()
        mediaSession?.release()
        musicPlayer.release()
        super.onDestroy()
    }

    private fun handleAction(action: String) {
        when (action) {
            ACTION_PLAY -> musicPlayer.play()
            ACTION_PAUSE -> musicPlayer.pause()
            ACTION_TOGGLE -> if (musicPlayer.isPlaying) musicPlayer.pause() else musicPlayer.play()
            ACTION_NEXT -> notifyNextRequested()
            ACTION_PREV -> notifyPrevRequested()
        }
    }

    var onNextRequested: (() -> Unit)? = null
    var onPrevRequested: (() -> Unit)? = null

    private fun notifyNextRequested() {
        onNextRequested?.invoke()
    }

    private fun notifyPrevRequested() {
        onPrevRequested?.invoke()
    }

    private fun setupMediaSession() {
        mediaSession = MediaSessionCompat(this, TAG).apply {
            setCallback(object : MediaSessionCompat.Callback() {
                override fun onPlay() { musicPlayer.play() }
                override fun onPause() { musicPlayer.pause() }
                override fun onSkipToNext() { notifyNextRequested() }
                override fun onSkipToPrevious() { notifyPrevRequested() }
                override fun onSeekTo(pos: Long) { musicPlayer.seekTo(pos.toInt()) }
            })
            isActive = true
        }
    }

    private fun updateMediaSession(song: Song?) {
        if (song == null) return
        val metadata = MediaMetadataCompat.Builder()
            .putString(MediaMetadataCompat.METADATA_KEY_TITLE, song.title)
            .putString(MediaMetadataCompat.METADATA_KEY_ARTIST, song.artist)
            .putString(MediaMetadataCompat.METADATA_KEY_ALBUM, song.album)
            .putLong(MediaMetadataCompat.METADATA_KEY_DURATION, song.duration)
            .build()
        mediaSession?.setMetadata(metadata)
        updatePlaybackState(musicPlayer.isPlaying)
    }

    private fun updatePlaybackState(playing: Boolean) {
        val state = if (playing) PlaybackStateCompat.STATE_PLAYING else PlaybackStateCompat.STATE_PAUSED
        mediaSession?.setPlaybackState(
            PlaybackStateCompat.Builder()
                .setState(state, musicPlayer.getCurrentPosition().toLong(), 1f)
                .setActions(
                    PlaybackStateCompat.ACTION_PLAY or
                    PlaybackStateCompat.ACTION_PAUSE or
                    PlaybackStateCompat.ACTION_SKIP_TO_NEXT or
                    PlaybackStateCompat.ACTION_SKIP_TO_PREVIOUS or
                    PlaybackStateCompat.ACTION_SEEK_TO
                )
                .build()
        )
    }

    fun updateNotification(song: Song?) {
        val notification = buildNotification(song)
        val nm = getSystemService(NotificationManager::class.java)
        nm.notify(NOTIFICATION_ID, notification)
    }

    private fun buildNotification(song: Song?): Notification {
        android.util.Log.d(TAG, "buildNotification song=${song?.title}")
        val openIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openPending = PendingIntent.getActivity(
            this, 0, openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val toggleIntent = Intent(this, PlayerService::class.java).apply { action = ACTION_TOGGLE }
        val nextIntent = Intent(this, PlayerService::class.java).apply { action = ACTION_NEXT }
        val prevIntent = Intent(this, PlayerService::class.java).apply { action = ACTION_PREV }

        val togglePending = PendingIntent.getService(this, 1, toggleIntent, PendingIntent.FLAG_IMMUTABLE)
        val nextPending = PendingIntent.getService(this, 2, nextIntent, PendingIntent.FLAG_IMMUTABLE)
        val prevPending = PendingIntent.getService(this, 3, prevIntent, PendingIntent.FLAG_IMMUTABLE)

        val title = song?.title ?: "MP3 Player"
        val text = song?.artist ?: "Reproduzindo música"
        val playIcon = if (musicPlayer.isPlaying) R.drawable.ic_pause else R.drawable.ic_play_arrow

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_play_arrow)
            .setLargeIcon(cachedAlbumArt)
            .setContentIntent(openPending)
            .setOngoing(true)
            .setStyle(MediaNotificationCompat.MediaStyle()
                .setMediaSession(mediaSession?.sessionToken)
                .setShowActionsInCompactView(0, 1, 2))
            .addAction(android.R.drawable.ic_media_previous, "Anterior", prevPending)
            .addAction(playIcon, "Play/Pause", togglePending)
            .addAction(android.R.drawable.ic_media_next, "Próximo", nextPending)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID, "MP3 Player", NotificationManager.IMPORTANCE_LOW
            ).apply { description = "Controles de reprodução" }
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(channel)
        }
    }

    private fun registerNoisyReceiver() {
        noisyReceiver = NoisyAudioReceiver()
        registerReceiver(noisyReceiver, IntentFilter(AudioManager.ACTION_AUDIO_BECOMING_NOISY))
    }

    private fun unregisterNoisyReceiver() {
        noisyReceiver?.let { try { unregisterReceiver(it) } catch (_: Exception) {} }
        noisyReceiver = null
    }

    private fun loadAlbumArt(path: String): Bitmap? {
        return try {
            MediaMetadataRetriever().use { r ->
                r.setDataSource(path)
                val data = r.embeddedPicture
                if (data != null) BitmapFactory.decodeByteArray(data, 0, data.size) else null
            }
        } catch (_: Exception) { null }
    }

    inner class NoisyAudioReceiver : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            android.util.Log.d(TAG, "NoisyAudioReceiver action=${intent?.action} isPlaying=${musicPlayer.isPlaying}")
            if (intent?.action == AudioManager.ACTION_AUDIO_BECOMING_NOISY && musicPlayer.isPlaying) {
                musicPlayer.pause()
            }
        }
    }

    companion object {
        const val CHANNEL_ID = "mp3_player_channel"
        const val NOTIFICATION_ID = 1
        const val TAG = "Mp3PlayerMediaSession"
        const val ACTION_TOGGLE = "com.mp3player.TOGGLE"
        const val ACTION_PLAY = "com.mp3player.PLAY"
        const val ACTION_PAUSE = "com.mp3player.PAUSE"
        const val ACTION_NEXT = "com.mp3player.NEXT"
        const val ACTION_PREV = "com.mp3player.PREV"
        const val ACTION_PLAY_STATE_CHANGED = "com.mp3player.PLAY_STATE_CHANGED"
    }
}
