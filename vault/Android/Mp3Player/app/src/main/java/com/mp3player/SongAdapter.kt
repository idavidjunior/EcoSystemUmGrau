package com.mp3player

import android.app.AlertDialog
import android.content.DialogInterface
import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.recyclerview.widget.RecyclerView
import com.mp3player.data.AlbumArtProvider
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

enum class ViewMode {
    DETAILED, COMPACT, CARD,
    LIST_LARGE, GRID, TEXT_ONLY, COVER_SMALL,
    EXPANDED, MINIMAL
}

enum class SortMode { TITLE, ARTIST, ALBUM, DURATION, DATE_ADDED, PLAY_COUNT }

class SongAdapter(
    private var songs: List<Song>,
    private val onItemClick: (Song) -> Unit
) : RecyclerView.Adapter<RecyclerView.ViewHolder>() {

    companion object {
        private const val VT_DETAILED = 0
        private const val VT_COMPACT = 1
        private const val VT_CARD = 2
        private const val VT_LIST_LARGE = 3
        private const val VT_GRID = 4
        private const val VT_TEXT_ONLY = 5
        private const val VT_COVER_SMALL = 6
        private const val VT_EXPANDED = 7
        private const val VT_MINIMAL = 8

        fun formatDuration(millis: Long): String {
            val totalSeconds = millis / 1000
            val minutes = totalSeconds / 60
            val seconds = totalSeconds % 60
            return String.format("%d:%02d", minutes, seconds)
        }

        fun sortSongs(songs: List<Song>, mode: SortMode, playCounts: Map<String, Int> = emptyMap()): List<Song> {
            return when (mode) {
                SortMode.TITLE -> songs.sortedBy { it.title.lowercase() }
                SortMode.ARTIST -> songs.sortedBy { it.artist.lowercase() }
                SortMode.ALBUM -> songs.sortedBy { it.album.lowercase() }
                SortMode.DURATION -> songs.sortedBy { it.duration }
                SortMode.DATE_ADDED -> songs.sortedByDescending { it.dateAdded }
                SortMode.PLAY_COUNT -> songs.sortedByDescending { playCounts[it.path] ?: 0 }
            }
        }
    }

    var currentSongPath: String? = null
        set(value) {
            if (field != value) {
                field = value
                notifyDataSetChanged()
            }
        }

    var viewMode: ViewMode = ViewMode.DETAILED
        set(value) {
            field = value
            notifyDataSetChanged()
        }

    private val scope = CoroutineScope(Dispatchers.Main + Job())
    var onAddToQueue: ((Song) -> Unit)? = null
    var onFavoriteClick: ((Song) -> Unit)? = null
    var onEditTag: ((Song) -> Unit)? = null
    var multiSelectMode = false
    val selectedSongs = mutableSetOf<Song>()
    var favoritePaths: MutableSet<String> = mutableSetOf()

    fun cleanup() { scope.cancel() }

    val currentList: List<Song> get() = songs

    fun updateSongs(newSongs: List<Song>) {
        songs = newSongs
        selectedSongs.clear()
        notifyDataSetChanged()
    }

    fun toggleMultiSelect() {
        multiSelectMode = !multiSelectMode
        selectedSongs.clear()
        notifyDataSetChanged()
    }

    fun getSelectedSongs(): List<Song> = songs.filter { it in selectedSongs }

    override fun getItemViewType(position: Int): Int {
        return when (viewMode) {
            ViewMode.COMPACT -> VT_COMPACT
            ViewMode.CARD -> VT_CARD
            ViewMode.LIST_LARGE -> VT_LIST_LARGE
            ViewMode.GRID -> VT_GRID
            ViewMode.TEXT_ONLY -> VT_TEXT_ONLY
            ViewMode.COVER_SMALL -> VT_COVER_SMALL
            ViewMode.EXPANDED -> VT_EXPANDED
            ViewMode.MINIMAL -> VT_MINIMAL
            else -> VT_DETAILED
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        val inflater = LayoutInflater.from(parent.context)
        return when (viewType) {
            VT_COMPACT -> CompactViewHolder(inflater.inflate(R.layout.song_item_compact, parent, false))
            VT_CARD -> CardViewHolder(inflater.inflate(R.layout.song_item_card, parent, false))
            VT_LIST_LARGE -> ListLargeViewHolder(inflater.inflate(R.layout.song_item_list_large, parent, false))
            VT_GRID -> GridViewHolder(inflater.inflate(R.layout.song_item_grid, parent, false))
            VT_TEXT_ONLY -> TextOnlyViewHolder(inflater.inflate(R.layout.song_item_text_only, parent, false))
            VT_COVER_SMALL -> CoverSmallViewHolder(inflater.inflate(R.layout.song_item_cover_small, parent, false))
            VT_EXPANDED -> ExpandedViewHolder(inflater.inflate(R.layout.song_item_expanded, parent, false))
            VT_MINIMAL -> MinimalViewHolder(inflater.inflate(R.layout.song_item_minimal, parent, false))
            else -> DetailedViewHolder(inflater.inflate(R.layout.song_item, parent, false))
        }
    }

    override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
        val song = songs[position]
        when (holder) {
            is DetailedViewHolder -> bindDetailed(holder, song, position)
            is CompactViewHolder -> bindCompact(holder, song, position)
            is CardViewHolder -> bindCard(holder, song, position)
            is ListLargeViewHolder -> bindListLarge(holder, song, position)
            is GridViewHolder -> bindGrid(holder, song, position)
            is TextOnlyViewHolder -> bindTextOnly(holder, song, position)
            is CoverSmallViewHolder -> bindCoverSmall(holder, song, position)
            is ExpandedViewHolder -> bindExpanded(holder, song, position)
            is MinimalViewHolder -> bindMinimal(holder, song, position)
        }
    }

    private fun setItemBackground(holder: RecyclerView.ViewHolder, song: Song) {
        val isNowPlaying = song.path == currentSongPath
        if (isNowPlaying) {
            holder.itemView.setBackgroundColor(Color.parseColor("#331DB954"))
        } else {
            holder.itemView.background = null
        }
    }

    private fun loadAlbumArtAsync(imageView: ImageView, path: String, context: android.content.Context) {
        scope.launch {
            val bmp = withContext(Dispatchers.IO) { AlbumArtProvider.getAlbumArt(path, context) }
            if (bmp != null) imageView.setImageBitmap(bmp)
        }
    }

    private fun bindExpanded(holder: ExpandedViewHolder, song: Song, position: Int) {
        holder.title.text = song.title
        holder.artist.text = song.artist
        holder.album.text = song.album
        holder.duration.text = formatDuration(song.duration)
        holder.albumArt.setImageResource(android.R.color.transparent)
        holder.itemView.alpha = if (multiSelectMode && song !in selectedSongs) 0.5f else 1.0f
        loadAlbumArtAsync(holder.albumArt, song.path, holder.itemView.context)
        bindCommon(holder, song, position)
        setItemBackground(holder, song)
    }

    private fun bindMinimal(holder: MinimalViewHolder, song: Song, position: Int) {
        holder.title.text = song.title
        holder.artist.text = song.artist
        holder.itemView.alpha = if (multiSelectMode && song !in selectedSongs) 0.5f else 1.0f
        bindCommon(holder, song, position)
        setItemBackground(holder, song)
    }

    private fun bindDetailed(holder: DetailedViewHolder, song: Song, position: Int) {
        holder.title.text = song.title
        holder.artist.text = song.artist
        holder.duration.text = formatDuration(song.duration)
        holder.albumArt.setImageResource(android.R.color.transparent)
        holder.itemView.alpha = if (multiSelectMode && song !in selectedSongs) 0.5f else 1.0f
        loadAlbumArtAsync(holder.albumArt, song.path, holder.itemView.context)
        bindCommon(holder, song, position)
        setItemBackground(holder, song)
    }

    private fun bindCompact(holder: CompactViewHolder, song: Song, position: Int) {
        holder.title.text = song.title
        holder.artist.text = song.artist
        holder.duration.text = formatDuration(song.duration)
        holder.itemView.alpha = if (multiSelectMode && song !in selectedSongs) 0.5f else 1.0f
        bindCommon(holder, song, position)
        setItemBackground(holder, song)
    }

    private fun bindCard(holder: CardViewHolder, song: Song, position: Int) {
        holder.title.text = song.title
        holder.artist.text = song.artist
        holder.album.text = song.album
        holder.duration.text = formatDuration(song.duration)
        holder.albumArt.setImageResource(android.R.color.transparent)
        loadAlbumArtAsync(holder.albumArt, song.path, holder.itemView.context)
        bindCommon(holder, song, position)
        val isNowPlaying = song.path == currentSongPath
        holder.cardBorder.setBackgroundColor(
            if (isNowPlaying) 0xFF1DB954.toInt() else android.R.color.transparent
        )
    }

    private fun bindListLarge(holder: ListLargeViewHolder, song: Song, position: Int) {
        holder.title.text = song.title
        holder.artist.text = song.artist
        holder.album.text = song.album
        holder.duration.text = formatDuration(song.duration)
        holder.albumArt.setImageResource(android.R.color.transparent)
        loadAlbumArtAsync(holder.albumArt, song.path, holder.itemView.context)
        bindCommon(holder, song, position)
        setItemBackground(holder, song)
    }

    private fun bindGrid(holder: GridViewHolder, song: Song, position: Int) {
        holder.title.text = song.title
        holder.artist.text = song.artist
        holder.albumArt.setImageResource(android.R.color.transparent)
        loadAlbumArtAsync(holder.albumArt, song.path, holder.itemView.context)
        bindCommon(holder, song, position)
    }

    private fun bindTextOnly(holder: TextOnlyViewHolder, song: Song, position: Int) {
        holder.title.text = song.title
        holder.artist.text = song.artist
        holder.duration.text = formatDuration(song.duration)
        holder.itemView.alpha = if (multiSelectMode && song !in selectedSongs) 0.5f else 1.0f
        bindCommon(holder, song, position)
        setItemBackground(holder, song)
    }

    private fun bindCoverSmall(holder: CoverSmallViewHolder, song: Song, position: Int) {
        holder.title.text = song.title
        holder.artist.text = song.artist
        holder.duration.text = formatDuration(song.duration)
        holder.albumArt.setImageResource(android.R.color.transparent)
        loadAlbumArtAsync(holder.albumArt, song.path, holder.itemView.context)
        bindCommon(holder, song, position)
        setItemBackground(holder, song)
    }

    private fun bindCommon(holder: RecyclerView.ViewHolder, song: Song, position: Int) {
        val favoriteIv: ImageView = holder.itemView.findViewById(R.id.iv_favorite)
        favoriteIv.setImageResource(
            if (song.path in favoritePaths) R.drawable.ic_favorite
            else R.drawable.ic_favorite_border
        )
        favoriteIv.setOnClickListener {
            val wasFav = song.path in favoritePaths
            if (wasFav) favoritePaths.remove(song.path) else favoritePaths.add(song.path)
            favoriteIv.setImageResource(
                if (wasFav) R.drawable.ic_favorite_border
                else R.drawable.ic_favorite
            )
            onFavoriteClick?.invoke(song)
        }

        holder.itemView.setOnClickListener {
            if (multiSelectMode) {
                if (song in selectedSongs) selectedSongs.remove(song) else selectedSongs.add(song)
                notifyItemChanged(position)
            } else {
                onItemClick(song)
            }
        }
        holder.itemView.setOnLongClickListener {
            if (!multiSelectMode) {
                val ctx = holder.itemView.context
                val items = arrayOf("Adicionar à fila", "Editar tags")
                AlertDialog.Builder(ctx)
                    .setTitle(song.title)
                    .setItems(items) { _: DialogInterface, which: Int ->
                        when (which) {
                            0 -> {
                                onAddToQueue?.invoke(song)
                                Toast.makeText(ctx, "Adicionado à fila: ${song.title}", Toast.LENGTH_SHORT).show()
                            }
                            1 -> onEditTag?.invoke(song)
                        }
                    }
                    .show()
            }
            true
        }
    }

    override fun getItemCount(): Int = songs.size

    class DetailedViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val albumArt: ImageView = view.findViewById(R.id.iv_album_art)
        val title: TextView = view.findViewById(R.id.tv_title)
        val artist: TextView = view.findViewById(R.id.tv_artist)
        val duration: TextView = view.findViewById(R.id.tv_duration)
    }

    class CompactViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val title: TextView = view.findViewById(R.id.tv_title)
        val artist: TextView = view.findViewById(R.id.tv_artist)
        val duration: TextView = view.findViewById(R.id.tv_duration)
    }

    class CardViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val albumArt: ImageView = view.findViewById(R.id.iv_card_album_art)
        val title: TextView = view.findViewById(R.id.tv_card_title)
        val artist: TextView = view.findViewById(R.id.tv_card_artist)
        val album: TextView = view.findViewById(R.id.tv_card_album)
        val duration: TextView = view.findViewById(R.id.tv_card_duration)
        val cardBorder: View = view.findViewById(R.id.card_border)
    }

    class ListLargeViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val albumArt: ImageView = view.findViewById(R.id.iv_list_large_art)
        val title: TextView = view.findViewById(R.id.tv_list_large_title)
        val artist: TextView = view.findViewById(R.id.tv_list_large_artist)
        val album: TextView = view.findViewById(R.id.tv_list_large_album)
        val duration: TextView = view.findViewById(R.id.tv_list_large_duration)
    }

    class GridViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val albumArt: ImageView = view.findViewById(R.id.iv_grid_art)
        val title: TextView = view.findViewById(R.id.tv_grid_title)
        val artist: TextView = view.findViewById(R.id.tv_grid_artist)
    }

    class TextOnlyViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val title: TextView = view.findViewById(R.id.tv_text_title)
        val artist: TextView = view.findViewById(R.id.tv_text_artist)
        val duration: TextView = view.findViewById(R.id.tv_text_duration)
    }

    class CoverSmallViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val albumArt: ImageView = view.findViewById(R.id.iv_cover_small_art)
        val title: TextView = view.findViewById(R.id.tv_cover_small_title)
        val artist: TextView = view.findViewById(R.id.tv_cover_small_artist)
        val duration: TextView = view.findViewById(R.id.tv_cover_small_duration)
    }

    class ExpandedViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val albumArt: ImageView = view.findViewById(R.id.iv_expanded_art)
        val title: TextView = view.findViewById(R.id.tv_expanded_title)
        val artist: TextView = view.findViewById(R.id.tv_expanded_artist)
        val album: TextView = view.findViewById(R.id.tv_expanded_album)
        val year: TextView = view.findViewById(R.id.tv_expanded_year)
        val duration: TextView = view.findViewById(R.id.tv_expanded_duration)
    }

    class MinimalViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val title: TextView = view.findViewById(R.id.tv_minimal_title)
        val artist: TextView = view.findViewById(R.id.tv_minimal_artist)
    }
}
