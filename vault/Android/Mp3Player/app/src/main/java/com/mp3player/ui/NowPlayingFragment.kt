package com.mp3player.ui

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.AudioManager
import android.media.MediaMetadataRetriever
import android.os.Bundle
import android.os.CountDownTimer
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.SeekBar
import android.widget.TextView
import android.widget.Button
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.mp3player.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class NowPlayingFragment : Fragment() {

    private var playerService: PlayerService? = null
    private var musicPlayer: MusicPlayer? = null
    private var audioManager: AudioManager? = null
    private var isSeeking = false
    private var sleepTimer: CountDownTimer? = null
    private var sleepTimerMinutes = 0
    private var albumArtCache = mutableMapOf<String, Bitmap?>()

    private val songChangeListener: (Song) -> Unit = { activity?.runOnUiThread { updateUI() } }
    private val playStateChangeListener: (Boolean) -> Unit = { playing ->
        activity?.runOnUiThread {
            btnPlayPause.setImageResource(if (playing) R.drawable.ic_pause else R.drawable.ic_play_arrow)
        }
    }

    private lateinit var btnBack: ImageButton
    private lateinit var btnQueue: ImageButton
    private lateinit var ivAlbumArt: ImageView
    private lateinit var tvTitle: TextView
    private lateinit var tvArtist: TextView
    private lateinit var tvAlbum: TextView
    private lateinit var tvCurrentTime: TextView
    private lateinit var tvTotalTime: TextView
    private lateinit var seekBar: SeekBar
    private lateinit var btnShuffle: ImageButton
    private lateinit var btnPrev: ImageButton
    private lateinit var btnPlayPause: ImageButton
    private lateinit var btnNext: ImageButton
    private lateinit var btnRepeat: ImageButton
    private lateinit var btnFavorite: ImageButton
    private lateinit var btnSleepTimer: ImageButton
    private lateinit var ivVolume: ImageView
    private lateinit var volumeSeekBar: SeekBar
    private lateinit var btnEqualizer: Button

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_now_playing, container, false)
        bindViews(v)
        audioManager = requireContext().getSystemService(android.content.Context.AUDIO_SERVICE) as AudioManager
        setupControls()
        return v
    }

    override fun onResume() {
        super.onResume()
        val act = activity as? MainActivity
        playerService = act?.playerService
        musicPlayer = playerService?.musicPlayer
        updateUI()
        startSeekBarUpdate()
        musicPlayer?.addSongChangedListener(songChangeListener)
        musicPlayer?.addPlayStateListener(playStateChangeListener)
    }

    override fun onPause() {
        super.onPause()
        seekBar.removeCallbacks(seekBarRunnable)
        musicPlayer?.removeSongChangedListener(songChangeListener)
        musicPlayer?.removePlayStateListener(playStateChangeListener)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        sleepTimer?.cancel()
        sleepTimer = null
    }

    private fun bindViews(v: View) {
        btnBack = v.findViewById(R.id.btn_back)
        btnQueue = v.findViewById(R.id.btn_queue)
        ivAlbumArt = v.findViewById(R.id.iv_album_art_large)
        tvTitle = v.findViewById(R.id.tv_song_title)
        tvArtist = v.findViewById(R.id.tv_song_artist)
        tvAlbum = v.findViewById(R.id.tv_song_album)
        tvCurrentTime = v.findViewById(R.id.tv_current_time)
        tvTotalTime = v.findViewById(R.id.tv_total_time)
        seekBar = v.findViewById(R.id.seek_bar)
        btnShuffle = v.findViewById(R.id.btn_shuffle)
        btnPrev = v.findViewById(R.id.btn_prev)
        btnPlayPause = v.findViewById(R.id.btn_play_pause)
        btnNext = v.findViewById(R.id.btn_next)
        btnRepeat = v.findViewById(R.id.btn_repeat)
        btnFavorite = v.findViewById(R.id.btn_favorite)
        btnSleepTimer = v.findViewById(R.id.btn_sleep_timer)
        ivVolume = v.findViewById(R.id.iv_volume_icon)
        volumeSeekBar = v.findViewById(R.id.volume_seekbar)
        btnEqualizer = v.findViewById(R.id.btn_equalizer)
    }

    private fun setupControls() {
        btnBack.setOnClickListener { parentFragmentManager.popBackStack() }

        btnQueue.setOnClickListener {
            val q = QueueBottomSheet()
            q.show(parentFragmentManager, "queue")
        }

        btnPlayPause.setOnClickListener {
            musicPlayer?.let { mp ->
                if (mp.isPlaying) { mp.pause() }
                else if (mp.isPrepared) { mp.play() }
            }
        }

        btnNext.setOnClickListener { (activity as? MainActivity)?.playNext() }
        btnPrev.setOnClickListener { (activity as? MainActivity)?.playPrevious() }

        btnShuffle.setOnClickListener {
            musicPlayer?.let { mp ->
                val mode = mp.toggleShuffle()
                btnShuffle.setColorFilter(if (mode == ShuffleMode.ON) 0xFF1DB954.toInt() else 0xFFFFFFFF.toInt())
                Toast.makeText(context, "Aleatório: ${if (mode == ShuffleMode.ON) "Ligado" else "Desligado"}", Toast.LENGTH_SHORT).show()
            }
        }

        btnRepeat.setOnClickListener {
            musicPlayer?.let { mp ->
                val mode = mp.toggleRepeat()
                val label = when (mode) {
                    RepeatMode.NONE -> "Desligado"
                    RepeatMode.ONE -> "Repetir 1"
                    RepeatMode.ALL -> "Repetir Tudo"
                }
                btnRepeat.setImageResource(
                    when (mode) {
                        RepeatMode.ONE -> R.drawable.ic_repeat_one
                        RepeatMode.ALL -> R.drawable.ic_repeat
                        RepeatMode.NONE -> R.drawable.ic_repeat
                    }
                )
                btnRepeat.setColorFilter(if (mode != RepeatMode.NONE) 0xFF1DB954.toInt() else 0xFFFFFFFF.toInt())
                Toast.makeText(context, "Repetir: $label", Toast.LENGTH_SHORT).show()
            }
        }

        btnFavorite.setOnClickListener {
            musicPlayer?.currentSong?.let { song ->
                lifecycleScope.launch {
                    val repo = com.mp3player.data.repository.MusicRepository(requireContext())
                    repo.toggleFavorite(song)
                    updateFavoriteIcon(song.path)
                }
            }
        }

        btnSleepTimer.setOnClickListener { showSleepTimerDialog() }

        btnEqualizer.setOnClickListener {
            val eq = EqualizerFragment()
            eq.show(parentFragmentManager, "equalizer")
        }

        seekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(sb: SeekBar?, p: Int, fromUser: Boolean) {
                if (fromUser) tvCurrentTime.text = formatTime(p.toLong())
            }
            override fun onStartTrackingTouch(sb: SeekBar?) { isSeeking = true }
            override fun onStopTrackingTouch(sb: SeekBar?) {
                isSeeking = false
                musicPlayer?.seekTo(sb?.progress ?: 0)
            }
        })

        audioManager?.let { am ->
            volumeSeekBar.max = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
            volumeSeekBar.progress = am.getStreamVolume(AudioManager.STREAM_MUSIC)
        }
        volumeSeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(sb: SeekBar?, p: Int, fromUser: Boolean) {
                if (fromUser) audioManager?.setStreamVolume(AudioManager.STREAM_MUSIC, p, 0)
            }
            override fun onStartTrackingTouch(sb: SeekBar?) {}
            override fun onStopTrackingTouch(sb: SeekBar?) {}
        })
    }

    private fun updateUI() {
        val song = musicPlayer?.currentSong
        if (song != null) {
            tvTitle.text = song.title
            tvArtist.text = song.artist
            tvAlbum.text = song.album
            loadAlbumArt(song.path)
            tvTotalTime.text = formatTime(musicPlayer?.getDuration()?.toLong() ?: 0)
            seekBar.max = musicPlayer?.getDuration() ?: 0
        }
        val playing = musicPlayer?.isPlaying == true
        btnPlayPause.setImageResource(if (playing) R.drawable.ic_pause else R.drawable.ic_play_arrow)

        musicPlayer?.let { mp ->
            btnShuffle.setColorFilter(if (mp.shuffleMode == ShuffleMode.ON) 0xFF1DB954.toInt() else 0xFFFFFFFF.toInt())
            btnRepeat.setImageResource(
                when (mp.repeatMode) {
                    RepeatMode.ONE -> R.drawable.ic_repeat_one
                    RepeatMode.ALL -> R.drawable.ic_repeat
                    RepeatMode.NONE -> R.drawable.ic_repeat
                }
            )
            btnRepeat.setColorFilter(if (mp.repeatMode != RepeatMode.NONE) 0xFF1DB954.toInt() else 0xFFFFFFFF.toInt())
        }
        song?.let { updateFavoriteIcon(it.path) }
    }

    private fun updateFavoriteIcon(songPath: String) {
        lifecycleScope.launch {
            val repo = com.mp3player.data.repository.MusicRepository(requireContext())
            val fav = repo.isFavoriteSync(songPath)
            btnFavorite.setColorFilter(if (fav) 0xFFFF4444.toInt() else 0xFFFFFFFF.toInt())
        }
    }

    private fun loadAlbumArt(path: String) {
        val cached = albumArtCache[path]
        if (cached != null) {
            ivAlbumArt.setImageBitmap(cached)
            return
        }
        lifecycleScope.launch {
            val bmp = withContext(Dispatchers.IO) {
                com.mp3player.data.AlbumArtProvider.getAlbumArt(path, requireContext())
            }
            if (bmp != null) {
                albumArtCache[path] = bmp
                ivAlbumArt.setImageBitmap(bmp)
            } else {
                ivAlbumArt.setImageResource(R.drawable.ic_launcher_foreground)
            }
        }
    }

    private val seekBarRunnable = object : Runnable {
        override fun run() {
            musicPlayer?.let { mp ->
                if (!isSeeking && mp.isPlaying) {
                    seekBar.progress = mp.getCurrentPosition()
                    tvCurrentTime.text = formatTime(mp.getCurrentPosition().toLong())
                    seekBar.postDelayed(this, 200)
                }
            }
        }
    }

    private fun startSeekBarUpdate() {
        seekBar.removeCallbacks(seekBarRunnable)
        seekBar.postDelayed(seekBarRunnable, 200)
    }

    private fun showSleepTimerDialog() {
        val options = arrayOf("Desligado", "15 min", "30 min", "45 min", "60 min", "90 min")
        val values = intArrayOf(0, 15, 30, 45, 60, 90)
        val checked = values.indexOf(sleepTimerMinutes)
        android.app.AlertDialog.Builder(requireContext())
            .setTitle("Sleep Timer")
            .setSingleChoiceItems(options, if (checked >= 0) checked else 0) { _, which ->
                sleepTimer?.cancel()
                sleepTimerMinutes = values[which]
                if (sleepTimerMinutes > 0) {
                    sleepTimer = object : CountDownTimer(sleepTimerMinutes * 60 * 1000L, 1000) {
                        override fun onTick(millisUntilFinished: Long) {}
                        override fun onFinish() {
                            musicPlayer?.pause()
                            btnPlayPause.setImageResource(R.drawable.ic_play_arrow)
                            btnSleepTimer.setColorFilter(0xFFFFFFFF.toInt())
                            Toast.makeText(context, "Sleep timer: reprodução pausada", Toast.LENGTH_SHORT).show()
                            sleepTimerMinutes = 0
                            sleepTimer = null
                        }
                    }.start()
                    btnSleepTimer.setColorFilter(0xFF1DB954.toInt())
                } else {
                    btnSleepTimer.setColorFilter(0xFFFFFFFF.toInt())
                }
            }
            .setPositiveButton("OK", null)
            .show()
    }

    private fun formatTime(millis: Long): String {
        val mins = java.util.concurrent.TimeUnit.MILLISECONDS.toMinutes(millis)
        val secs = java.util.concurrent.TimeUnit.MILLISECONDS.toSeconds(millis) % 60
        return String.format("%d:%02d", mins, secs)
    }
}
