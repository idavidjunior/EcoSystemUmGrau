package com.mp3player

import android.Manifest
import android.app.AlertDialog
import android.content.ComponentName
import android.content.Context
import android.content.DialogInterface
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.database.Cursor
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.AudioManager
import android.util.LruCache
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.CountDownTimer
import android.os.Environment
import android.os.Handler
import android.os.IBinder
import android.provider.MediaStore
import android.provider.Settings
import android.text.Editable
import android.text.TextWatcher
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.SeekBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.material.snackbar.Snackbar
import com.mp3player.data.EqStateLoader
import com.mp3player.data.PlayCountManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    private lateinit var bottomNav: BottomNavigationView
    private lateinit var fragmentContainer: androidx.fragment.app.FragmentContainerView

    private lateinit var btnPlayPause: ImageButton
    private lateinit var btnNext: ImageButton
    private lateinit var btnPrev: ImageButton
    private lateinit var btnShuffle: ImageButton
    private lateinit var btnRepeat: ImageButton
    private lateinit var seekBar: SeekBar
    private lateinit var tvCurrentTime: TextView
    private lateinit var tvTotalTime: TextView
    private lateinit var tvSongTitle: TextView
    private lateinit var tvSongArtist: TextView
    private lateinit var ivAlbumArt: ImageView
    private lateinit var ivVolumeIcon: ImageView
    private lateinit var volumeSeekBar: SeekBar
    private lateinit var btnExpandPlayer: ImageButton
    private lateinit var expandedControls: View
    private lateinit var btnSleepTimer: ImageButton
    private lateinit var playerPanel: View
    private lateinit var etSearch: EditText

    // Mini player controls (collapsed state)
    private lateinit var btnMiniPrev: ImageButton
    private lateinit var btnMiniPlayPause: ImageButton
    private lateinit var btnMiniNext: ImageButton

    private var playerExpanded = false
    private var albumArtCache = object : LruCache<String, Bitmap>(50 * 1024 * 1024) {
        override fun sizeOf(key: String, value: Bitmap): Int = value.byteCount
    }
    private var sleepTimer: CountDownTimer? = null
    private var sleepTimerMinutes = 0
    private var currentPlaylist: List<Song> = emptyList()
    private var audioManager: AudioManager? = null
    private var isVolumeChanging = false
    private lateinit var playerPanelDivider: View

    var playerService: PlayerService? = null
        private set
    private var bound = false
    val songs = mutableListOf<Song>()
    val playCountManager: PlayCountManager by lazy { PlayCountManager(this) }
    private var currentIndex = -1
    private var isSeeking = false
    private var pendingPermission = false
    private var searchQuery = ""
    private val seekBarUpdater = object : Runnable {
        override fun run() { updateSeekBar() }
    }

    private val tagEditorLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
        if (it.resultCode == RESULT_OK) {
            loadSongs()
        }
    }

    fun openTagEditor(song: Song) {
        val intent = Intent(this, TagEditorActivity::class.java).apply {
            putExtra("song_id", song.id)
            putExtra("song_path", song.path)
            putExtra("song_title", song.title)
            putExtra("song_artist", song.artist)
            putExtra("song_album", song.album)
        }
        tagEditorLauncher.launch(intent)
    }

    private val contentObserver = object : android.database.ContentObserver(Handler()) {
        override fun onChange(selfChange: Boolean) {
            if (!pendingPermission && hasRequiredPermission()) {
                loadSongs()
            }
        }
    }

    private lateinit var songsFragment: SongsFragment
    private lateinit var albumsFragment: AlbumsFragment
    private lateinit var artistsFragment: ArtistsFragment
    private lateinit var foldersFragment: FoldersFragment
    private lateinit var settingsFragment: SettingsFragment

    private val connection = object : ServiceConnection {
        private var playStateListener: ((Boolean) -> Unit)? = null
        private var songChangedListener: ((Song) -> Unit)? = null

        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            android.util.Log.d(TAG, "=== onServiceConnected ===")
            val binder = service as PlayerService.LocalBinder
            playerService = binder.getService()
            bound = true
            playStateListener?.let { playerService?.musicPlayer?.removePlayStateListener(it) }
            songChangedListener?.let { playerService?.musicPlayer?.removeSongChangedListener(it) }
            playStateListener = { playing ->
                runOnUiThread {
                    val icon = if (playing) R.drawable.ic_pause else R.drawable.ic_play_arrow
                    btnPlayPause.setImageResource(icon)
                    btnMiniPlayPause.setImageResource(icon)
                }
            }
            songChangedListener = { song ->
                runOnUiThread {
                    tvSongTitle.text = song.title
                    tvSongArtist.text = song.artist
                    loadAlbumArt(song.path)
                }
            }
            playerService?.musicPlayer?.addPlayStateListener(playStateListener!!)
            playerService?.musicPlayer?.addSongChangedListener(songChangedListener!!)
            playerService?.onNextRequested = { runOnUiThread { playNext() } }
            playerService?.onPrevRequested = { runOnUiThread { playPrevious() } }
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            android.util.Log.d(TAG, "=== onServiceDisconnected ===")
            playerService = null
            bound = false
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        val prefs = getSharedPreferences("mp3player_prefs", 0)
        if (prefs.getString("theme", "dark") == "light") {
            setTheme(R.style.Theme_App_Light)
        }
        super.onCreate(savedInstanceState)
        android.util.Log.d(TAG, "=== ACTIVITY onCreate savedInstanceState=$savedInstanceState ===")
        setContentView(R.layout.activity_main)

        bindViews()
        setupFragments()
        setupBottomNav()
        setupControls()

        supportFragmentManager.addOnBackStackChangedListener {
            syncViewVisibility()
        }

        if (savedInstanceState == null) {
            checkAndRequestPermissions()
        }
    }

    override fun onStart() {
        super.onStart()
        android.util.Log.d(TAG, "=== ACTIVITY onStart bound=$bound ===")
        val intent = Intent(this, PlayerService::class.java)
        ContextCompat.startForegroundService(this, intent)
        bindService(intent, connection, Context.BIND_AUTO_CREATE)
    }

    override fun onStop() {
        super.onStop()
        android.util.Log.d(TAG, "=== ACTIVITY onStop bound=$bound ===")
        if (bound) {
            unbindService(connection)
            bound = false
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        sleepTimer?.cancel()
        sleepTimer = null
        seekBar.removeCallbacks(seekBarUpdater)
    }

    fun hasRequiredPermission(): Boolean {
        return when {
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU ->
                ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_AUDIO) == PackageManager.PERMISSION_GRANTED
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.R ->
                Environment.isExternalStorageManager()
            else ->
                ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED
        }
    }

    override fun onResume() {
        super.onResume()
        android.util.Log.d(TAG, "=== ACTIVITY onResume ===")
        syncViewVisibility()
        if (!pendingPermission && hasRequiredPermission()) {
            loadSongs()
        }
        contentResolver.registerContentObserver(
            MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
            true,
            contentObserver
        )
    }

    private fun syncViewVisibility() {
        val backCount = supportFragmentManager.backStackEntryCount
        if (backCount > 0) {
            val name = supportFragmentManager.getBackStackEntryAt(backCount - 1).name
            when (name) {
                "now_playing" -> {
                    playerPanel.visibility = View.GONE
                    playerPanelDivider.visibility = View.GONE
                    etSearch.visibility = View.GONE
                }
                "album_detail", "artist_detail" -> {
                    playerPanel.visibility = View.VISIBLE
                    playerPanelDivider.visibility = View.VISIBLE
                    etSearch.visibility = View.GONE
                }
                else -> {
                    playerPanel.visibility = View.VISIBLE
                    playerPanelDivider.visibility = View.VISIBLE
                }
            }
        } else {
            playerPanel.visibility = View.VISIBLE
            playerPanelDivider.visibility = View.VISIBLE
            etSearch.visibility = if (bottomNav.selectedItemId == R.id.nav_songs) View.VISIBLE else View.GONE
        }
        bottomNav.visibility = View.VISIBLE
    }

    override fun onPause() {
        super.onPause()
        android.util.Log.d(TAG, "=== ACTIVITY onPause ===")
        contentResolver.unregisterContentObserver(contentObserver)
    }

    private fun bindViews() {
        bottomNav = findViewById(R.id.bottom_navigation)
        fragmentContainer = findViewById(R.id.fragment_container)
        btnPlayPause = findViewById(R.id.btn_play_pause)
        btnNext = findViewById(R.id.btn_next)
        btnPrev = findViewById(R.id.btn_prev)
        btnShuffle = findViewById(R.id.btn_shuffle)
        btnRepeat = findViewById(R.id.btn_repeat)
        seekBar = findViewById(R.id.seek_bar)
        tvCurrentTime = findViewById(R.id.tv_current_time)
        tvTotalTime = findViewById(R.id.tv_total_time)
        tvSongTitle = findViewById(R.id.tv_song_title)
        tvSongArtist = findViewById(R.id.tv_song_artist)
        ivAlbumArt = findViewById(R.id.iv_album_art)
        ivVolumeIcon = findViewById(R.id.iv_volume_icon)
        volumeSeekBar = findViewById(R.id.volume_seekbar)
        btnExpandPlayer = findViewById(R.id.btn_expand_player)
        expandedControls = findViewById(R.id.expanded_controls)
        btnSleepTimer = findViewById(R.id.btn_sleep_timer)
        playerPanel = findViewById(R.id.player_panel)
        playerPanelDivider = findViewById(R.id.player_panel_divider)
        etSearch = findViewById(R.id.et_search)

        // Mini player controls
        btnMiniPrev = findViewById(R.id.btn_mini_prev)
        btnMiniPlayPause = findViewById(R.id.btn_mini_play_pause)
        btnMiniNext = findViewById(R.id.btn_mini_next)

        audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        if (audioManager != null) {
            val maxVol = audioManager!!.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
            volumeSeekBar.max = maxVol
            volumeSeekBar.progress = audioManager!!.getStreamVolume(AudioManager.STREAM_MUSIC)
        }
    }

    private fun setupFragments() {
        songsFragment = SongsFragment()
        albumsFragment = AlbumsFragment()
        artistsFragment = ArtistsFragment()
        foldersFragment = FoldersFragment()
        settingsFragment = SettingsFragment().apply {
            setOnRescan {
                if (hasRequiredPermission()) {
                    loadSongs()
                } else {
                    checkAndRequestPermissions()
                }
            }
        }
    }

    private fun setupBottomNav() {
        bottomNav.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_songs -> {
                    etSearch.visibility = View.VISIBLE
                    switchFragment(songsFragment)
                }
                R.id.nav_albums -> {
                    etSearch.visibility = View.GONE
                    switchFragment(albumsFragment)
                }
                R.id.nav_artists -> {
                    etSearch.visibility = View.GONE
                    switchFragment(artistsFragment)
                }
                R.id.nav_folders -> {
                    etSearch.visibility = View.GONE
                    switchFragment(foldersFragment)
                }
                R.id.nav_settings -> {
                    etSearch.visibility = View.GONE
                    switchFragment(settingsFragment)
                }
            }
            true
        }
        bottomNav.selectedItemId = R.id.nav_songs
    }

    private fun switchFragment(f: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragment_container, f)
            .commitNow()
    }

    fun playSongFromList(songsList: List<Song>, index: Int) {
        if (index !in songsList.indices) return

        playerService?.musicPlayer?.let { mp ->
            val song = songsList[index]
            val isSameSong = mp.currentSong?.path == song.path && mp.isPrepared

            if (isSameSong) {
                if (mp.isPlaying) {
                    mp.pause()
                    btnPlayPause.setImageResource(R.drawable.ic_play_arrow)
                    btnMiniPlayPause.setImageResource(R.drawable.ic_play_arrow)
                } else {
                    mp.play()
                    btnPlayPause.setImageResource(R.drawable.ic_pause)
                    btnMiniPlayPause.setImageResource(R.drawable.ic_pause)
                }
                return
            }

            currentIndex = index
            currentPlaylist = songsList.toList()

            playCountManager.incrementPlayCount(song.path)

            playerPanel.visibility = View.VISIBLE
            playerPanelDivider.visibility = View.VISIBLE

            mp.setPlaylist(songsList)
            tvSongTitle.text = song.title
            tvSongArtist.text = song.artist
            loadAlbumArt(song.path)

            EqStateLoader.restoreTo(mp, this)

            songsFragment.setCurrentSongPath(song.path)

            mp.playSong(
                song = song,
                onPrepared = {
                    runOnUiThread {
                        btnPlayPause.setImageResource(R.drawable.ic_pause)
                        btnMiniPlayPause.setImageResource(R.drawable.ic_pause)
                        seekBar.max = mp.getDuration()
                        tvTotalTime.text = formatTime(mp.getDuration().toLong())
                        updateSeekBar()
                    }
                },
                onCompletion = {
                    runOnUiThread {
                        if (sleepTimer != null) {
                            sleepTimer?.cancel()
                            sleepTimer = null
                            sleepTimerMinutes = 0
                            btnSleepTimer.setColorFilter(0xFFFFFFFF.toInt())
                        }
                        playNext()
                    }
                }
            )
        }
    }

    private fun loadAlbumArt(path: String) {
        val cached = albumArtCache.get(path)
        if (cached != null) {
            ivAlbumArt.setImageBitmap(cached)
            return
        }
        CoroutineScope(Dispatchers.Main).launch {
            val bmp = withContext(Dispatchers.IO) {
                com.mp3player.data.AlbumArtProvider.getAlbumArt(path, this@MainActivity)
            }
            if (bmp != null) {
                albumArtCache.put(path, bmp)
                ivAlbumArt.setImageBitmap(bmp)
            } else {
                ivAlbumArt.setImageResource(R.drawable.ic_launcher_foreground)
            }
        }
    }

    private fun setupControls() {
        // Mini player controls (collapsed state)
        btnMiniPlayPause.setOnClickListener {
            playerService?.musicPlayer?.let { mp ->
                if (mp.isPlaying) {
                    mp.pause()
                } else if (mp.isPrepared) {
                    mp.play()
                }
            }
        }
        btnMiniPrev.setOnClickListener { playPrevious() }
        btnMiniNext.setOnClickListener { playNext() }

        // Expanded player controls
        btnPlayPause.setOnClickListener {
            playerService?.musicPlayer?.let { mp ->
                if (mp.isPlaying) {
                    mp.pause()
                } else if (mp.isPrepared) {
                    mp.play()
                }
            }
        }

        btnNext.setOnClickListener { playNext() }
        btnPrev.setOnClickListener { playPrevious() }

        btnShuffle.setOnClickListener {
            playerService?.musicPlayer?.let { mp ->
                val mode = mp.toggleShuffle()
                val isOn = mode == ShuffleMode.ON
                btnShuffle.setColorFilter(if (isOn) 0xFF1DB954.toInt() else 0xFFFFFFFF.toInt())
                Toast.makeText(this, "Aleatório: ${if (isOn) "Ligado" else "Desligado"}", Toast.LENGTH_SHORT).show()
            }
        }

        btnRepeat.setOnClickListener {
            playerService?.musicPlayer?.let { mp ->
                val mode = mp.toggleRepeat()
                val label = when (mode) {
                    RepeatMode.NONE -> "Desligado"
                    RepeatMode.ONE -> "Repetir 1"
                    RepeatMode.ALL -> "Repetir Tudo"
                }
                val icon = when (mode) {
                    RepeatMode.ONE -> R.drawable.ic_repeat_one
                    RepeatMode.ALL -> R.drawable.ic_repeat
                    RepeatMode.NONE -> R.drawable.ic_repeat
                }
                btnRepeat.setImageResource(icon)
                btnRepeat.setColorFilter(
                    if (mode != RepeatMode.NONE) 0xFF1DB954.toInt() else 0xFFFFFFFF.toInt()
                )
                Toast.makeText(this, "Repetir: $label", Toast.LENGTH_SHORT).show()
            }
        }

        seekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(sb: SeekBar?, p: Int, fromUser: Boolean) {
                if (fromUser) tvCurrentTime.text = formatTime(p.toLong())
            }
            override fun onStartTrackingTouch(sb: SeekBar?) { isSeeking = true }
            override fun onStopTrackingTouch(sb: SeekBar?) {
                isSeeking = false
                playerService?.musicPlayer?.seekTo(sb?.progress ?: 0)
            }
        })

        btnExpandPlayer.setOnClickListener {
            playerExpanded = !playerExpanded
            expandedControls.visibility = if (playerExpanded) View.VISIBLE else View.GONE
            btnExpandPlayer.setImageResource(
                if (playerExpanded) android.R.drawable.arrow_down_float
                else android.R.drawable.arrow_up_float
            )
        }

        volumeSeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(sb: SeekBar?, p: Int, fromUser: Boolean) {
                if (fromUser) {
                    audioManager?.setStreamVolume(AudioManager.STREAM_MUSIC, p, 0)
                    updateVolumeIcon(p)
                }
            }
            override fun onStartTrackingTouch(sb: SeekBar?) { isVolumeChanging = true }
            override fun onStopTrackingTouch(sb: SeekBar?) { isVolumeChanging = false }
        })

        btnSleepTimer.setOnClickListener {
            showSleepTimerDialog()
        }

        playerPanel.setOnClickListener { openNowPlaying() }

        setupSearch()
    }

    private fun updateVolumeIcon(progress: Int) {
        ivVolumeIcon.setImageResource(
            when {
                progress == 0 -> android.R.drawable.ic_lock_silent_mode
                else -> android.R.drawable.ic_lock_silent_mode_off
            }
        )
    }

    private fun showSleepTimerDialog() {
        val options = arrayOf("Desligado", "15 min", "30 min", "45 min", "60 min", "90 min")
        val values = intArrayOf(0, 15, 30, 45, 60, 90)
        val checked = values.indexOf(sleepTimerMinutes)

        AlertDialog.Builder(this)
            .setTitle("Sleep Timer")
            .setSingleChoiceItems(options, if (checked >= 0) checked else 0) { _, which ->
                sleepTimer?.cancel()
                sleepTimerMinutes = values[which]
                if (sleepTimerMinutes > 0) {
                    val millis = sleepTimerMinutes * 60 * 1000L
                    sleepTimer = object : CountDownTimer(millis, 1000) {
                        override fun onTick(millisUntilFinished: Long) {}
                        override fun onFinish() {
                            runOnUiThread {
                                playerService?.musicPlayer?.pause()
                                btnPlayPause.setImageResource(R.drawable.ic_play_arrow)
                                btnMiniPlayPause.setImageResource(R.drawable.ic_play_arrow)
                                btnSleepTimer.setColorFilter(0xFFFFFFFF.toInt())
                                Toast.makeText(this@MainActivity, "Sleep timer: reprodução pausada", Toast.LENGTH_SHORT).show()
                            }
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

    private fun setupSearch() {
        etSearch.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                searchQuery = s?.toString()?.lowercase() ?: ""
                filterSongs()
            }
        })
    }

    private fun filterSongs() {
        if (searchQuery.isBlank()) {
            songsFragment.setSongs(songs) { song ->
                val idx = songs.indexOf(song)
                if (idx >= 0) playSongFromList(songs, idx)
            }
            return
        }
        val filtered = songs.filter { song ->
            song.title.lowercase().contains(searchQuery) ||
            song.artist.lowercase().contains(searchQuery) ||
            song.album.lowercase().contains(searchQuery)
        }
        songsFragment.setSongs(filtered) { song ->
            val idx = filtered.indexOf(song)
            if (idx >= 0) playSongFromList(filtered, idx)
        }
    }

    fun playNext() {
        if (currentPlaylist.isEmpty()) return
        playerService?.musicPlayer?.let { mp ->
            val next = mp.getNextIndex(currentIndex)
            if (next >= 0 && next < currentPlaylist.size) {
                playSongFromList(currentPlaylist, next)
            }
        }
    }

    fun playPrevious() {
        if (currentPlaylist.isEmpty()) return
        playerService?.musicPlayer?.let { mp ->
            val prev = mp.getPrevIndex(currentIndex)
            if (prev >= 0 && prev < currentPlaylist.size) {
                playSongFromList(currentPlaylist, prev)
            }
        }
    }

    fun openNowPlaying() {
        if (supportFragmentManager.backStackEntryCount > 0 &&
            supportFragmentManager.getBackStackEntryAt(supportFragmentManager.backStackEntryCount - 1).name == "now_playing") {
            return
        }
        try {
            val frag = com.mp3player.ui.NowPlayingFragment()
            supportFragmentManager.beginTransaction()
                .replace(R.id.fragment_container, frag)
                .addToBackStack("now_playing")
                .commit()
            playerPanel.visibility = View.GONE
            playerPanelDivider.visibility = View.GONE
            etSearch.visibility = View.GONE
        } catch (e: Exception) {
            e.printStackTrace()
            android.util.Log.e(TAG, "openNowPlaying crashed", e)
        }
    }

    private fun updateSeekBar() {
        val mp = playerService?.musicPlayer ?: return
        if (!isSeeking && mp.isPlaying) {
            seekBar.progress = mp.getCurrentPosition()
            tvCurrentTime.text = formatTime(mp.getCurrentPosition().toLong())
        }
        if (mp.isPlaying) {
            seekBar.postDelayed(seekBarUpdater, 200)
        }
    }

    private fun checkAndRequestPermissions() {
        when {
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.R -> {
                if (Environment.isExternalStorageManager()) {
                    requestMediaPermission()
                } else {
                    showManageStorageDialog()
                }
            }
            ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE)
                == PackageManager.PERMISSION_GRANTED -> loadSongs()
            ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.READ_EXTERNAL_STORAGE) ->
                showLegacyRationaleDialog()
            else -> requestLegacyPermission()
        }
    }

    private fun showManageStorageDialog() {
        AlertDialog.Builder(this)
            .setTitle("Permissão de gerenciamento de arquivos")
            .setMessage(
                "Para acessar todas as suas músicas, o MP3 Player precisa da " +
                "permissão \"Gerenciar todos os arquivos\".\n\n" +
                "Toque em \"Permitir\" e ative a chave na tela seguinte."
            )
            .setPositiveButton("Permitir") { _: DialogInterface, _: Int ->
                startActivityForResult(
                    Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).apply {
                        data = Uri.parse("package:$packageName")
                    },
                    MANAGE_STORAGE_REQUEST_CODE
                )
            }
            .setNegativeButton("Negar") { _: DialogInterface, _: Int ->
                Toast.makeText(this, "Permissão negada. O app não funcionará.", Toast.LENGTH_LONG).show()
            }
            .setCancelable(false)
            .show()
    }

    private fun requestMediaPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_AUDIO)
                == PackageManager.PERMISSION_GRANTED
            ) {
                loadSongs()
            } else {
                pendingPermission = true
                ActivityCompat.requestPermissions(
                    this, arrayOf(Manifest.permission.READ_MEDIA_AUDIO), PERMISSION_REQUEST_CODE
                )
            }
        } else {
            loadSongs()
        }
    }

    private fun showLegacyRationaleDialog() {
        AlertDialog.Builder(this)
            .setTitle("Permissão necessária")
            .setMessage(
                "O MP3 Player precisa acessar suas músicas para funcionar.\n\n" +
                "Permita o acesso à biblioteca de áudio para:\n" +
                "• Listar todas as suas músicas\n" +
                "• Ler metadados (título, artista, álbum)\n" +
                "• Reproduzir os arquivos de áudio"
            )
            .setPositiveButton("Permitir") { _: DialogInterface, _: Int -> requestLegacyPermission() }
            .setNegativeButton("Negar") { _: DialogInterface, _: Int ->
                Snackbar.make(findViewById(android.R.id.content),
                    "Permissão negada. O app não funcionará corretamente.",
                    Snackbar.LENGTH_LONG).show()
            }
            .setCancelable(false)
            .show()
    }

    private fun requestLegacyPermission() {
        pendingPermission = true
        ActivityCompat.requestPermissions(
            this, arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE), PERMISSION_REQUEST_CODE
        )
    }

    @Suppress("DEPRECATION")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == MANAGE_STORAGE_REQUEST_CODE) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && Environment.isExternalStorageManager()) {
                requestMediaPermission()
            } else {
                AlertDialog.Builder(this)
                    .setTitle("Permissão necessária")
                    .setMessage("Você precisa ativar \"Gerenciar todos os arquivos\" para o MP3 Player acessar suas músicas.")
                    .setPositiveButton("Tentar novamente") { _, _ -> checkAndRequestPermissions() }
                    .setNegativeButton("Sair") { _, _ -> finish() }
                    .setCancelable(false)
                    .show()
            }
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<out String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            pendingPermission = false
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                loadSongs()
            } else {
                AlertDialog.Builder(this)
                    .setTitle("Permissão bloqueada")
                    .setMessage("A permissão foi negada. Vá em Configurações > Aplicativos > MP3 Player > Permissões e ative manualmente.")
                    .setPositiveButton("Abrir Configurações") { _, _ ->
                        startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                            data = Uri.parse("package:$packageName")
                        })
                    }
                    .setNegativeButton("Fechar", null)
                    .show()
            }
        }
    }

    fun loadSongs() {
        if (!hasRequiredPermission()) return
        lifecycleScope.launch {
            val rawList = withContext(Dispatchers.IO) { querySongs() }
            val filtered = applyFilters(rawList)
            songs.clear()
            songs.addAll(filtered)

            val onPlay: (Song) -> Unit = { song ->
                val idx = songs.indexOf(song)
                if (idx >= 0) playSongFromList(songs, idx)
            }

            songsFragment.setSongs(songs, onPlay)

            val albums = songs.groupBy { it.album to it.artist }.map { (key, list) ->
                AlbumItem(name = key.first, artist = key.second, songCount = list.size, songs = list)
            }.sortedBy { it.name }
            albumsFragment.setAlbums(albums) { item ->
                openAlbumDetail(item)
            }

            val artists = songs.groupBy { it.artist }
                .filterKeys { !it.isNullOrBlank() && it != "<unknown>" && it != "Desconhecido" }
                .map { (name, list) ->
                    ArtistItem(name = name, albumCount = list.distinctBy { it.album }.size, songCount = list.size, songs = list)
                }.sortedBy { it.name }
            artistsFragment.setArtists(artists) { item ->
                openArtistDetail(item)
            }

            val folders = songs.groupBy { it.folder }.map { (path, list) ->
                val name = path.substringAfterLast('/').ifEmpty { "/" }
                FolderItem(path = path, name = name, songCount = list.size, songs = list)
            }.sortedBy { it.name }
            foldersFragment.setFolders(folders, if (folders.isNotEmpty()) folders.first().path else "/") { item ->
                if (item.songs.isNotEmpty()) playSongFromList(item.songs, 0)
            }

            settingsFragment.setStats(songs.size, artists.size, albums.size)
        }
    }

    private fun querySongs(): List<Song> {
        val collection = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL)
        } else {
            MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
        }
        val projection = arrayOf(
            MediaStore.Audio.Media._ID,
            MediaStore.Audio.Media.TITLE,
            MediaStore.Audio.Media.ARTIST,
            MediaStore.Audio.Media.ALBUM,
            MediaStore.Audio.Media.DURATION,
            MediaStore.Audio.Media.DATA,
            MediaStore.Audio.Media.DATE_ADDED
        )
        val selection = "${MediaStore.Audio.Media.IS_MUSIC} != 0"
        val sortOrder = "${MediaStore.Audio.Media.TITLE} ASC"

        try {
            val rawList = mutableListOf<Song>()
            contentResolver.query(collection, projection, selection, null, sortOrder)?.use { c ->
                val idCol = c.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
                val titleCol = c.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE)
                val artistCol = c.getColumnIndexOrThrow(MediaStore.Audio.Media.ARTIST)
                val albumCol = c.getColumnIndexOrThrow(MediaStore.Audio.Media.ALBUM)
                val durCol = c.getColumnIndexOrThrow(MediaStore.Audio.Media.DURATION)
                val dataCol = c.getColumnIndexOrThrow(MediaStore.Audio.Media.DATA)
                val dateCol = c.getColumnIndexOrThrow(MediaStore.Audio.Media.DATE_ADDED)

                while (c.moveToNext()) {
                    val path = c.getString(dataCol) ?: ""
                    var title = c.getString(titleCol)
                    var artist = c.getString(artistCol)
                    var album = c.getString(albumCol)
                    val duration = c.getLong(durCol)
                    val dateAdded = c.getLong(dateCol)

                    if (title.isNullOrBlank() || title == "<unknown>" || artist.isNullOrBlank() || artist == "<unknown>" || album.isNullOrBlank() || album == "<unknown>") {
                        val meta = readMetadataFromFile(path)
                        if (title.isNullOrBlank() || title == "<unknown>") title = meta.first
                        if (artist.isNullOrBlank() || artist == "<unknown>") artist = meta.second
                        if (album.isNullOrBlank() || album == "<unknown>") album = meta.third
                    }

                    rawList.add(Song(
                        id = c.getLong(idCol),
                        title = if (title.isNullOrBlank() || title == "<unknown>") path.substringAfterLast('/').substringBeforeLast('.') else title,
                        artist = if (artist.isNullOrBlank() || artist == "<unknown>") "Desconhecido" else artist,
                        album = if (album.isNullOrBlank() || album == "<unknown>") "Desconhecido" else album,
                        duration = duration,
                        path = path,
                        dateAdded = dateAdded
                    ))
                }
            }
            return rawList
        } catch (e: Exception) {
            e.printStackTrace()
            runOnUiThread {
                Snackbar.make(findViewById(android.R.id.content), "Erro ao carregar músicas: ${e.message}", Snackbar.LENGTH_LONG).show()
            }
            return emptyList()
        }
    }

    private fun applyFilters(rawSongs: List<Song>): List<Song> {
        val prefs = getSharedPreferences("mp3player_prefs", 0)
        val minSizeKb = prefs.getString("min_size_kb", "500")?.toIntOrNull() ?: 500
        val minDurationSec = prefs.getString("min_duration_sec", "30")?.toIntOrNull() ?: 30
        val scanFolder = prefs.getString("scan_folder", "") ?: ""

        return rawSongs.filter { song ->
            val sizeOk = try {
                java.io.File(song.path).length() / 1024 >= minSizeKb
            } catch (_: Exception) { true }
            val durationOk = song.duration / 1000 >= minDurationSec
            val folderOk = scanFolder.isBlank() || song.path.startsWith(scanFolder)
            sizeOk && durationOk && folderOk
        }
    }

    private fun openAlbumDetail(item: AlbumItem) {
        val frag = AlbumDetailFragment()
        frag.setAlbum(item.name, item.artist, item.songs) { song ->
            val idx = item.songs.indexOf(song)
            if (idx >= 0) playSongFromList(item.songs, idx)
        }
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragment_container, frag)
            .addToBackStack("album_detail")
            .commit()
        etSearch.visibility = View.GONE
    }

    private fun openArtistDetail(item: ArtistItem) {
        val frag = ArtistDetailFragment()
        frag.setArtist(item.name, item.albumCount, item.songs) { song ->
            val idx = item.songs.indexOf(song)
            if (idx >= 0) playSongFromList(item.songs, idx)
        }
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragment_container, frag)
            .addToBackStack("artist_detail")
            .commit()
        etSearch.visibility = View.GONE
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (supportFragmentManager.backStackEntryCount > 0) {
            supportFragmentManager.popBackStack()
            syncViewVisibility()
        } else {
            super.onBackPressed()
        }
    }

    private fun readMetadataFromFile(path: String): Triple<String?, String?, String?> {
        if (path.isBlank()) return Triple(null, null, null)
        return try {
            MediaMetadataRetriever().use { retriever ->
                retriever.setDataSource(path)
                val title = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_TITLE)
                val artist = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ARTIST)
                val album = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ALBUM)
                Triple(title, artist, album)
            }
        } catch (e: Exception) {
            Triple(null, null, null)
        }
    }

    private fun formatTime(millis: Long): String {
        val mins = TimeUnit.MILLISECONDS.toMinutes(millis)
        val secs = TimeUnit.MILLISECONDS.toSeconds(millis) % 60
        return String.format("%d:%02d", mins, secs)
    }

    companion object {
        private const val PERMISSION_REQUEST_CODE = 100
        private const val MANAGE_STORAGE_REQUEST_CODE = 101
        private const val TAG = "Mp3Player.MainActivity"
    }
}
