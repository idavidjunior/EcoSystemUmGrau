package com.mp3player

import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.google.android.material.textfield.TextInputEditText
import com.mp3player.data.AlbumArtProvider
import com.mp3player.data.StorageHelper
import com.mp3player.data.model.MusicMetadata
import com.mp3player.data.online.MetadataSearchService
import com.mp3player.data.online.SearchMode
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withContext
import com.mp3player.data.tagging.FallbackTagProcessor
import java.io.File

class TagEditorActivity : AppCompatActivity() {

    private lateinit var tvFileName: TextView
    private lateinit var ivAlbumArt: ImageView
    private lateinit var btnSearchOnline: Button
    private lateinit var etTitle: TextInputEditText
    private lateinit var etArtist: TextInputEditText
    private lateinit var etAlbum: TextInputEditText
    private lateinit var etYear: TextInputEditText
    private lateinit var etTrack: TextInputEditText
    private lateinit var etGenre: TextInputEditText
    private lateinit var btnCancel: Button
    private lateinit var btnSave: Button

    private var songId: Long = -1
    private var songPath: String = ""
    private var songTitle: String = ""
    private var songArtist: String = ""
    private var songAlbum: String = ""

    private var embeddedArtBytes: ByteArray? = null
    private var embeddedArtMime = "image/jpeg"
    private var isSearching = false

    private fun isUnknownValue(value: String?): Boolean {
        if (value.isNullOrBlank()) return true
        val v = value.trim()
        return v.isEmpty() || v.equals("Desconhecido", ignoreCase = true) ||
               v.equals("<unknown>", ignoreCase = true) || v.length < 2
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        val prefs = getSharedPreferences("mp3player_prefs", 0)
        if (prefs.getString("theme", "dark") == "light") {
            setTheme(R.style.Theme_App_Light)
        }
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_tag_editor)

        songId = intent.getLongExtra("song_id", -1)
        songPath = intent.getStringExtra("song_path") ?: ""
        songTitle = intent.getStringExtra("song_title") ?: ""
        songArtist = intent.getStringExtra("song_artist") ?: ""
        songAlbum = intent.getStringExtra("song_album") ?: ""

        if (songId == -1L || songPath.isBlank()) {
            Toast.makeText(this, "Erro: dados da música inválidos", Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        bindViews()
        loadCurrentMetadata()
        setupListeners()
    }

    private fun bindViews() {
        tvFileName = findViewById(R.id.tv_file_name)
        ivAlbumArt = findViewById(R.id.iv_album_art_preview)
        btnSearchOnline = findViewById(R.id.btn_search_online)
        etTitle = findViewById(R.id.et_title)
        etArtist = findViewById(R.id.et_artist)
        etAlbum = findViewById(R.id.et_album)
        etYear = findViewById(R.id.et_year)
        etTrack = findViewById(R.id.et_track)
        etGenre = findViewById(R.id.et_genre)
        btnCancel = findViewById(R.id.btn_cancel)
        btnSave = findViewById(R.id.btn_save)

        tvFileName.text = songPath.substringAfterLast('/')
    }

    private fun loadCurrentMetadata() {
        lifecycleScope.launch(Dispatchers.IO) {
            var meta = FallbackTagProcessor.getInstance().read(File(songPath))
            if (meta == null || !meta.isComplete) {
                try {
                    MediaMetadataRetriever().use { r ->
                        r.setDataSource(songPath)
                        val mmrTitle = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_TITLE)
                        val mmrArtist = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ARTIST)
                        val mmrAlbum = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ALBUM)
                        val mmrYear = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_YEAR)
                        val mmrGenre = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_GENRE)
                        val mmrTrack = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_CD_TRACK_NUMBER)

                        val existing = meta
                        val t = existing?.title ?: mmrTitle?.ifBlank { null }
                        val a = existing?.artist ?: mmrArtist?.ifBlank { null }
                        val al = existing?.album ?: mmrAlbum?.ifBlank { null }
                        if (t != null || a != null || al != null) {
                            meta = MusicMetadata(
                                title = t, artist = a, album = al,
                                year = existing?.year ?: mmrYear?.ifBlank { null },
                                genre = existing?.genre ?: mmrGenre?.ifBlank { null },
                                trackNumber = existing?.trackNumber ?: mmrTrack?.ifBlank { null },
                                albumArtBytes = existing?.albumArtBytes ?: r.embeddedPicture,
                                albumArtMime = existing?.albumArtMime ?: "image/jpeg"
                            )
                        }
                    }
                } catch (_: Exception) {}
            }

            if (meta == null) {
                val artRetriever = try {
                    MediaMetadataRetriever().use { it.setDataSource(songPath); it.embeddedPicture }
                } catch (_: Exception) { null }
                val folderBytes = if (artRetriever == null) AlbumArtProvider.findCoverBytes(songPath) else null
                withContext(Dispatchers.Main) {
                    val cleanedTitle = MetadataSearchService.cleanQuery(songTitle)
                    val extractedArtist = if (songArtist == "Desconhecido" || songArtist.isBlank()) {
                        MetadataSearchService.extractArtistFromFilename(songPath)
                    } else null
                    // Strip artist prefix from title when we extracted it from filename
                    val finalTitle = if (extractedArtist != null) {
                        MetadataSearchService.cleanQuery(
                            songTitle.replace(Regex("^" + java.util.regex.Pattern.quote(extractedArtist) + "\\s*[-–—|]\\s*", RegexOption.IGNORE_CASE), "")
                        )
                    } else cleanedTitle
                    etTitle.setText(finalTitle.ifBlank { cleanedTitle.ifBlank { songTitle } })
                    etArtist.setText(extractedArtist ?: songArtist)
                    etAlbum.setText(songAlbum)
                    embeddedArtBytes = artRetriever ?: folderBytes
                    embeddedArtMime = "image/jpeg"
                    embeddedArtBytes?.let { b ->
                        BitmapFactory.decodeByteArray(b, 0, b.size)?.let { ivAlbumArt.setImageBitmap(it) }
                    }
                }
                return@launch
            }

            withContext(Dispatchers.Main) {
                etTitle.setText(meta?.title ?: songTitle)
                etArtist.setText(meta?.artist ?: songArtist)
                etAlbum.setText(meta?.album ?: songAlbum)
                meta?.year?.let { etYear.setText(it) }
                meta?.genre?.let { etGenre.setText(it) }
                meta?.trackNumber?.let { etTrack.setText(it) }
                meta?.albumArtBytes?.let { bytes ->
                    embeddedArtBytes = bytes
                    embeddedArtMime = meta?.albumArtMime ?: "image/jpeg"
                    BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.let { ivAlbumArt.setImageBitmap(it) }
                }
                if (embeddedArtBytes == null) {
                    val folderBytes = AlbumArtProvider.findCoverBytes(songPath)
                    if (folderBytes != null) {
                        embeddedArtBytes = folderBytes
                        BitmapFactory.decodeByteArray(folderBytes, 0, folderBytes.size)?.let { ivAlbumArt.setImageBitmap(it) }
                    }
                }
            }
        }
    }

    private fun setupListeners() {
        btnSearchOnline.setOnClickListener {
            if (isSearching) return@setOnClickListener
            searchOnline()
        }

        btnSave.setOnClickListener { saveMetadata() }
        btnCancel.setOnClickListener { finish() }
    }

    private fun searchOnline(mode: SearchMode = SearchMode.NORMAL) {
        val rawTitle = etTitle.text?.toString()?.trim()?.ifBlank { null } ?: songTitle
        val rawArtist = etArtist.text?.toString()?.trim()?.ifBlank { null } ?: songArtist
        val rawAlbum = etAlbum.text?.toString()?.trim()?.ifBlank { null } ?: songAlbum

        // Track which fields already have real data — won't overwrite them with search results
        val knownTitle = !isUnknownValue(rawTitle)
        val knownArtist = !isUnknownValue(rawArtist)
        val knownAlbum = !isUnknownValue(rawAlbum)
        val knownYear = !isUnknownValue(etYear.text?.toString()?.trim())
        val knownGenre = !isUnknownValue(etGenre.text?.toString()?.trim())
        val knownTrack = !isUnknownValue(etTrack.text?.toString()?.trim())

        val queryTitle = MetadataSearchService.cleanQuery(rawTitle)
        val queryArtist = MetadataSearchService.cleanQuery(rawArtist)
        val queryAlbum = MetadataSearchService.cleanQuery(rawAlbum)

        if (queryTitle.isBlank() && queryArtist.isBlank()) {
            Toast.makeText(this, "Informe ao menos o título ou artista para buscar", Toast.LENGTH_SHORT).show()
            return
        }

        isSearching = true
        btnSearchOnline.text = if (mode == SearchMode.RELAXED) "Buscando (tentativa 2)..." else "Buscando..."
        btnSearchOnline.isEnabled = false

        lifecycleScope.launch {
            try {
                val result = MetadataSearchService.searchAll(queryTitle, queryArtist, queryAlbum, songPath, this@TagEditorActivity, mode)
                withContext(Dispatchers.Main) {
                    if (result != null && (result.title != null || result.artist != null || result.album != null)) {
                        // Merge: prefer known (existing) fields over search results
                        val merged = MusicMetadata(
                            title = if (knownTitle) rawTitle else result.title,
                            artist = if (knownArtist) rawArtist else result.artist,
                            album = if (knownAlbum) rawAlbum else result.album,
                            year = if (knownYear) etYear.text?.toString()?.trim() else result.year,
                            genre = if (knownGenre) etGenre.text?.toString()?.trim() else result.genre,
                            trackNumber = if (knownTrack) etTrack.text?.toString()?.trim() else result.trackNumber,
                            albumArtBytes = result.albumArtBytes,
                            albumArtMime = result.albumArtMime
                        )
                        showSearchConfirmation(result, merged, rawTitle, rawArtist, rawAlbum, mode)
                    } else {
                        val msg = if (mode == SearchMode.RELAXED)
                            "Nada encontrado. Tente editar manualmente os campos e buscar novamente."
                        else
                            "Nada encontrado para \"$queryTitle\""
                        Toast.makeText(this@TagEditorActivity, msg, Toast.LENGTH_LONG).show()
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    Toast.makeText(this@TagEditorActivity, "Erro na busca: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            } finally {
                withContext(Dispatchers.Main) {
                    isSearching = false
                    btnSearchOnline.text = "Buscar na Internet"
                    btnSearchOnline.isEnabled = true
                }
            }
        }
    }

    private fun showSearchConfirmation(rawResult: MusicMetadata, merged: MusicMetadata,
                                       currentTitle: String, currentArtist: String, currentAlbum: String,
                                       mode: SearchMode = SearchMode.NORMAL) {
        val msg = buildString {
            if (merged.title != null) {
                if (merged.title != currentTitle) append("Titulo: ${merged.title} (novo!)\n")
                else append("Titulo: ${merged.title} (mantido)\n")
            }
            if (merged.artist != null) {
                if (merged.artist != currentArtist) append("Artista: ${merged.artist} (novo!)\n")
                else append("Artista: ${merged.artist} (mantido)\n")
            }
            if (merged.album != null) {
                if (merged.album != currentAlbum) append("Album: ${merged.album} (novo!)\n")
                else append("Album: ${merged.album} (mantido)\n")
            }
            if (merged.year != null) append("Ano: ${merged.year}\n")
            if (merged.genre != null) append("Genero: ${merged.genre}\n")
            if (merged.trackNumber != null) append("Faixa: ${merged.trackNumber}\n")
        }
        val builder = AlertDialog.Builder(this)
            .setTitle("Metadados encontrados")
            .setMessage("Aplicar as informacoes abaixo?\n\n$msg")
            .setPositiveButton("Aplicar") { _, _ ->
                merged.title?.let { etTitle.setText(it) }
                merged.artist?.let { etArtist.setText(it) }
                merged.album?.let { etAlbum.setText(it) }
                merged.year?.let { etYear.setText(it) }
                merged.genre?.let { etGenre.setText(it) }
                merged.trackNumber?.let { etTrack.setText(it) }
                if (rawResult.albumArtBytes != null) {
                    embeddedArtBytes = rawResult.albumArtBytes
                    embeddedArtMime = rawResult.albumArtMime ?: "image/jpeg"
                    val bmp = BitmapFactory.decodeByteArray(rawResult.albumArtBytes, 0, rawResult.albumArtBytes.size)
                    if (bmp != null) {
                        ivAlbumArt.setImageBitmap(bmp)
                        Toast.makeText(this, "Arte do album encontrada!", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    Toast.makeText(this, "Arte do album nao encontrada", Toast.LENGTH_SHORT).show()
                }
                Toast.makeText(this, "Metadados aplicados! Clique em SALVAR para persistir.", Toast.LENGTH_LONG).show()
            }
            .setNegativeButton("Descartar", null)
        // Only show "Tentar Novamente" on NORMAL mode searches
        if (mode == SearchMode.NORMAL) {
            builder.setNeutralButton("Tentar Novamente") { _, _ ->
                searchOnline(SearchMode.RELAXED)
            }
        }
        builder.show()
    }

    private fun saveMetadata() {
        val title = etTitle.text?.toString()?.trim().let { if (it.isNullOrBlank()) songTitle else it }
        val artist = etArtist.text?.toString()?.trim().let { if (it.isNullOrBlank()) songArtist else it }
        val album = etAlbum.text?.toString()?.trim().let { if (it.isNullOrBlank()) songAlbum else it }
        val year = etYear.text?.toString()?.trim().let { if (it.isNullOrBlank()) null else it }
        val genre = etGenre.text?.toString()?.trim().let { if (it.isNullOrBlank()) null else it }
        val track = etTrack.text?.toString()?.trim().let { if (it.isNullOrBlank()) null else it }

        val metadata = MusicMetadata(
            title = title,
            artist = artist,
            album = album,
            year = year,
            genre = genre,
            trackNumber = track,
            albumArtBytes = embeddedArtBytes,
            albumArtMime = embeddedArtMime
        )

        btnSave.isEnabled = false
        btnSave.text = "Salvando..."

        lifecycleScope.launch(Dispatchers.IO) {
            val ok = StorageHelper.writeTagsSafe(this@TagEditorActivity, songId, songPath, metadata)
            withContext(Dispatchers.Main) {
                btnSave.isEnabled = true
                btnSave.text = "Salvar"
                if (ok) {
                    Toast.makeText(this@TagEditorActivity, "Metadados salvos com sucesso!", Toast.LENGTH_SHORT).show()
                    setResult(RESULT_OK)
                    finish()
                } else {
                    AlertDialog.Builder(this@TagEditorActivity)
                        .setTitle("Erro ao salvar")
                        .setMessage("Não foi possível salvar os metadados.\n\n" +
                                "Certifique-se de que o app tem permissão de gerenciamento de arquivos " +
                                "(Configurações > Aplicativos > MP3 Player > Permissões > " +
                                "Gerenciar todos os arquivos).")
                        .setPositiveButton("OK", null)
                        .show()
                }
            }
        }
    }
}
