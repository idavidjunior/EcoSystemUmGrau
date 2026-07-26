package com.mp3player

import android.content.Context
import android.media.AudioManager
import android.net.Uri
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.common.audio.AudioProcessor
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.RenderersFactory
import androidx.media3.exoplayer.audio.MediaCodecAudioRenderer
import androidx.media3.exoplayer.mediacodec.MediaCodecSelector
import com.mp3player.data.audio.EqualizerAudioProcessor
import java.io.File
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.random.Random

enum class RepeatMode { NONE, ONE, ALL }
enum class ShuffleMode { OFF, ON }

@OptIn(UnstableApi::class)
class MusicPlayer(private val context: Context) {

    var equalizerProcessor: EqualizerAudioProcessor? = null

    private var exoPlayer: ExoPlayer? = null
    val audioSessionId: Int get() = exoPlayer?.audioSessionId ?: 0
    var currentSong: Song? = null
    var isPlaying: Boolean = false
        private set
    var isPrepared: Boolean = false
        private set

    var repeatMode: RepeatMode = RepeatMode.ALL
    var shuffleMode: ShuffleMode = ShuffleMode.OFF

    private var songList: List<Song> = emptyList()
    private var shuffledIndices: MutableList<Int> = mutableListOf()
    private var shuffleIndex: Int = 0

    private val queue = mutableListOf<Song>()
    private var queueIndex = -1

    private val songChangedListeners = CopyOnWriteArrayList<(Song) -> Unit>()
    private val playStateListeners = CopyOnWriteArrayList<(Boolean) -> Unit>()
    private val queueChangedListeners = CopyOnWriteArrayList<() -> Unit>()

    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private var audioFocusHeld = false

    private val audioFocusChangeListener = AudioManager.OnAudioFocusChangeListener { focusChange ->
        when (focusChange) {
            AudioManager.AUDIOFOCUS_LOSS -> { if (isPlaying) pause(); abandonAudioFocus() }
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT -> { if (isPlaying) pause() }
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK -> { exoPlayer?.volume = 0.3f }
            AudioManager.AUDIOFOCUS_GAIN -> {
                exoPlayer?.volume = 1.0f
            }
        }
    }

    private fun requestAudioFocus(): Boolean {
        val result = audioManager.requestAudioFocus(
            audioFocusChangeListener, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN
        )
        audioFocusHeld = result == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
        return audioFocusHeld
    }

    private fun abandonAudioFocus() {
        if (audioFocusHeld) {
            audioManager.abandonAudioFocus(audioFocusChangeListener)
            audioFocusHeld = false
        }
    }

    init {
        val eqProc = EqualizerAudioProcessor()
        equalizerProcessor = eqProc
        val renderersFactory = RenderersFactory { handler, videoListener, audioListener, textOutput, metadataOutput ->
            arrayOf(
                MediaCodecAudioRenderer(
                    context,
                    MediaCodecSelector.DEFAULT,
                    handler,
                    audioListener,
                    androidx.media3.exoplayer.audio.AudioCapabilities.DEFAULT_AUDIO_CAPABILITIES,
                    eqProc as AudioProcessor
                )
            )
        }
        exoPlayer = ExoPlayer.Builder(context)
            .setRenderersFactory(renderersFactory)
            .build()
            .apply {
            addListener(object : Player.Listener {
                override fun onIsPlayingChanged(playing: Boolean) {
                    this@MusicPlayer.isPlaying = playing
                    playStateListeners.forEach { it(playing) }
                }

                override fun onPlaybackStateChanged(state: Int) {
                    when (state) {
                        Player.STATE_READY -> {
                            isPrepared = true
                            currentSong?.let { song -> songChangedListeners.forEach { listener -> listener(song) } }
                            onPreparedCallback?.invoke()
                            onPreparedCallback = null
                        }
                        Player.STATE_ENDED -> {
                            isPrepared = false
                            if (this@MusicPlayer.repeatMode == RepeatMode.ONE) {
                                seekTo(0)
                                play()
                            } else {
                                onCompletionCallbacks.forEach { it() }
                            }
                        }
                        Player.STATE_IDLE -> {
                            isPrepared = false
                        }
                    }
                }

                override fun onPlayerError(error: PlaybackException) {
                    isPrepared = false
                    error.printStackTrace()
                }
            })
        }
    }

    private val onCompletionCallbacks = mutableListOf<() -> Unit>()
    private var onPreparedCallback: (() -> Unit)? = null

    fun addSongChangedListener(l: (Song) -> Unit) { songChangedListeners.add(l) }
    fun removeSongChangedListener(l: (Song) -> Unit) { songChangedListeners.remove(l) }
    fun addPlayStateListener(l: (Boolean) -> Unit) { playStateListeners.add(l) }
    fun removePlayStateListener(l: (Boolean) -> Unit) { playStateListeners.remove(l) }
    fun addQueueChangedListener(l: () -> Unit) { queueChangedListeners.add(l) }
    fun removeQueueChangedListener(l: () -> Unit) { queueChangedListeners.remove(l) }

    fun setPlaylist(songs: List<Song>) {
        songList = songs
        buildShuffleOrder()
    }

    private fun buildShuffleOrder() {
        shuffledIndices = songList.indices.toMutableList()
        shuffledIndices.shuffle(Random)
        shuffleIndex = 0
    }

    fun getNextIndex(currentIdx: Int): Int {
        if (queue.isNotEmpty()) {
            val nextIdx = queueIndex + 1
            if (nextIdx in queue.indices) {
                queueIndex = nextIdx
                val song = queue[nextIdx]
                val idx = songList.indexOfFirst { it.path == song.path }
                if (idx >= 0) return idx
            }
            queue.clear()
            queueIndex = -1
        }
        return getNextFromList(currentIdx)
    }

    private fun getNextFromList(currentIdx: Int): Int {
        return when {
            songList.isEmpty() -> -1
            repeatMode == RepeatMode.ONE -> currentIdx
            shuffleMode == ShuffleMode.ON -> {
                if (shuffledIndices.isEmpty()) buildShuffleOrder()
                val idx = shuffledIndices.getOrElse(shuffleIndex) { 0 }
                shuffleIndex = (shuffleIndex + 1) % shuffledIndices.size
                idx
            }
            else -> (currentIdx + 1) % songList.size
        }
    }

    fun getPrevIndex(currentIdx: Int): Int {
        return when {
            songList.isEmpty() -> -1
            repeatMode == RepeatMode.ONE -> currentIdx
            shuffleMode == ShuffleMode.ON -> {
                if (shuffledIndices.isEmpty()) buildShuffleOrder()
                shuffleIndex = (shuffleIndex - 1 + shuffledIndices.size) % shuffledIndices.size
                shuffledIndices[shuffleIndex]
            }
            else -> (currentIdx - 1 + songList.size) % songList.size
        }
    }

    fun getQueueIndex(): Int = queueIndex

    fun toggleShuffle(): ShuffleMode {
        shuffleMode = if (shuffleMode == ShuffleMode.OFF) ShuffleMode.ON else ShuffleMode.OFF
        if (shuffleMode == ShuffleMode.ON) buildShuffleOrder()
        return shuffleMode
    }

    fun toggleRepeat(): RepeatMode {
        repeatMode = when (repeatMode) {
            RepeatMode.NONE -> RepeatMode.ALL
            RepeatMode.ALL -> RepeatMode.ONE
            RepeatMode.ONE -> RepeatMode.NONE
        }
        return repeatMode
    }

    fun addToQueue(song: Song) {
        queue.add(song)
        queueChangedListeners.forEach { it() }
    }

    fun removeFromQueue(index: Int) {
        if (index in queue.indices) {
            queue.removeAt(index)
            if (queueIndex >= queue.size) queueIndex = queue.size - 1
        }
        queueChangedListeners.forEach { it() }
    }

    fun moveQueueItem(fromIndex: Int, toIndex: Int) {
        if (fromIndex in queue.indices && toIndex in queue.indices) {
            val item = queue.removeAt(fromIndex)
            queue.add(toIndex, item)
            queueChangedListeners.forEach { it() }
        }
    }

    fun clearQueue() {
        queue.clear()
        queueIndex = -1
        queueChangedListeners.forEach { it() }
    }

    fun getQueue(): List<Song> = queue.toList()

    fun playSong(song: Song, onPrepared: () -> Unit = {}, onCompletion: () -> Unit = {}) {
        currentSong = song
        isPrepared = false
        onPreparedCallback = onPrepared

        if (!requestAudioFocus()) return

        val uri = Uri.fromFile(File(song.path))
        val mediaItem = MediaItem.Builder()
            .setUri(uri)
            .setMediaMetadata(
                MediaMetadata.Builder()
                    .setTitle(song.title)
                    .setArtist(song.artist)
                    .setAlbumTitle(song.album)
                    .build()
            )
            .build()

        exoPlayer?.let { player ->
            player.stop()
            player.clearMediaItems()
            player.setMediaItem(mediaItem)
            player.prepare()
            player.play()
        }

        onCompletionCallbacks.clear()
        onCompletionCallbacks.add(onCompletion)
    }

    fun play() {
        exoPlayer?.let {
            if (!it.playWhenReady) {
                if (!audioFocusHeld && !requestAudioFocus()) return
                it.play()
            }
        }
    }

    fun pause() {
        exoPlayer?.let {
            if (it.playWhenReady) {
                it.pause()
            }
        }
    }

    fun seekTo(position: Int) {
        exoPlayer?.seekTo(position.toLong())
    }

    fun getCurrentPosition(): Int = exoPlayer?.currentPosition?.toInt() ?: 0

    fun getDuration(): Int = exoPlayer?.duration?.toInt() ?: 0

    fun setEqBandGain(bandId: Int, gainDb: Float) {
        equalizerProcessor?.setBandGain(bandId, gainDb)
    }

    fun setEqPreampGain(gainDb: Float) {
        equalizerProcessor?.setPreampGain(gainDb)
    }

    fun resetEq() {
        equalizerProcessor?.resetAllBands()
    }

    fun applyEqPreset(gains: FloatArray, preamp: Float) {
        equalizerProcessor?.applyPreset(gains, preamp)
    }

    fun release() {
        abandonAudioFocus()
        exoPlayer?.release()
        exoPlayer = null
        isPlaying = false
        isPrepared = false
        currentSong = null
        songList = emptyList()
        queue.clear()
        queueIndex = -1
        songChangedListeners.clear()
        playStateListeners.clear()
        queueChangedListeners.clear()
    }
}
