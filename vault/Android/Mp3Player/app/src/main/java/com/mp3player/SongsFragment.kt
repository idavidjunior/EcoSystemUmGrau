package com.mp3player

import android.content.SharedPreferences
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.mp3player.data.PlayCountManager
import com.mp3player.data.repository.MusicRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class SongsFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var tvEmpty: TextView
    private lateinit var adapter: SongAdapter
    private lateinit var btnFilterAll: Button
    private lateinit var btnFilterFav: Button
    private lateinit var btnSort: Button
    private lateinit var btnViewMode: Button
    private lateinit var btnMultiSelect: Button
    private lateinit var btnAddSelected: Button

    private var allSongs: List<Song> = emptyList()
    private var onSongClick: ((Song) -> Unit)? = null
    private var showFavoritesOnly = false
    private var repository: MusicRepository? = null
    private var prefs: SharedPreferences? = null
    private var filterJob: Job? = null

    private var currentSort: SortMode = SortMode.TITLE
    private var currentView: ViewMode = ViewMode.DETAILED
    private var currentSongPath: String? = null

    private val sortLabels = mapOf(
        SortMode.TITLE to "A-Z",
        SortMode.ARTIST to "Art.",
        SortMode.ALBUM to "Alb.",
        SortMode.DURATION to "Dur.",
        SortMode.DATE_ADDED to "Data",
        SortMode.PLAY_COUNT to "Top"
    )

    private val sortOptions = listOf(SortMode.TITLE, SortMode.ARTIST, SortMode.ALBUM, SortMode.DURATION, SortMode.DATE_ADDED, SortMode.PLAY_COUNT)

    private val sortDialogLabels = arrayOf("Nome (A-Z)", "Artista", "Álbum", "Duração", "Data de adição", "Mais Tocadas")

    fun setSongs(songs: List<Song>, onPlay: (Song) -> Unit) {
        allSongs = songs
        onSongClick = onPlay
        applyFilter()
    }

    fun setCurrentSongPath(path: String?) {
        currentSongPath = path
        if (::adapter.isInitialized) {
            adapter.currentSongPath = path
            scrollToCurrentSong()
        }
    }

    private fun scrollToCurrentSong() {
        val path = currentSongPath ?: return
        val idx = adapter.currentList.indexOfFirst { it.path == path }
        if (idx >= 0) {
            recyclerView.smoothScrollToPosition(idx)
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_songs, container, false)
        recyclerView = v.findViewById(R.id.recycler_songs)
        swipeRefresh = v.findViewById(R.id.swipe_refresh)
        tvEmpty = v.findViewById(R.id.tv_empty)
        btnFilterAll = v.findViewById(R.id.btn_filter_all)
        btnFilterFav = v.findViewById(R.id.btn_filter_favorites)
        btnSort = v.findViewById(R.id.btn_sort)
        btnViewMode = v.findViewById(R.id.btn_view_mode)
        btnMultiSelect = v.findViewById(R.id.btn_multi_select)
        btnAddSelected = v.findViewById(R.id.btn_add_selected)

        repository = MusicRepository(requireContext())
        prefs = requireContext().getSharedPreferences("mp3player_prefs", 0)

        currentSort = SortMode.valueOf(prefs?.getString("sort_mode", "TITLE") ?: "TITLE")
        currentView = ViewMode.valueOf(prefs?.getString("view_mode", "DETAILED") ?: "DETAILED")

        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        adapter = SongAdapter(emptyList<Song>()) { song ->
            if (!adapter.multiSelectMode) {
                onSongClick?.invoke(song)
            } else {
                adapter.selectedSongs.let {
                    if (song in it) it.remove(song) else it.add(song)
                    adapter.notifyDataSetChanged()
                    val count = it.size
                    btnAddSelected.text = "+$count"
                    btnAddSelected.visibility = if (count > 0) View.VISIBLE else View.GONE
                }
            }
        }
        adapter.onAddToQueue = { song ->
            val act = activity as? MainActivity
            act?.playerService?.musicPlayer?.addToQueue(song)
            Toast.makeText(context, "Adicionado à fila: ${song.title}", Toast.LENGTH_SHORT).show()
        }
        adapter.onFavoriteClick = { song ->
            lifecycleScope.launch(Dispatchers.IO) {
                repository?.toggleFavorite(song)
            }
        }
        adapter.onEditTag = { song ->
            (activity as? MainActivity)?.openTagEditor(song)
        }
        adapter.viewMode = currentView
        adapter.currentSongPath = currentSongPath
        recyclerView.adapter = adapter
        applyFilter()

        btnFilterAll.setOnClickListener {
            showFavoritesOnly = false
            btnFilterAll.setBackgroundResource(R.drawable.btn_filter_active)
            btnFilterFav.setBackgroundResource(R.drawable.btn_filter_inactive)
            exitMultiSelect()
            applyFilter()
        }

        btnFilterFav.setOnClickListener {
            showFavoritesOnly = true
            btnFilterFav.setBackgroundResource(R.drawable.btn_filter_active)
            btnFilterAll.setBackgroundResource(R.drawable.btn_filter_inactive)
            exitMultiSelect()
            applyFilter()
        }

        btnSort.setOnClickListener {
            val cur = sortOptions.indexOf(currentSort)
            android.app.AlertDialog.Builder(requireContext())
                .setTitle("Ordenar por")
                .setSingleChoiceItems(sortDialogLabels, cur) { _, which ->
                    currentSort = sortOptions[which]
                    prefs?.edit()?.putString("sort_mode", currentSort.name)?.apply()
                    btnSort.text = sortLabels[currentSort]
                    applyFilter()
                }
                .setPositiveButton("OK", null)
                .show()
        }

        btnViewMode.setOnClickListener {
            val modes = ViewMode.entries.toList()
            val cur = modes.indexOf(currentView)
            val labels = arrayOf("Lista detalhada", "Lista compacta", "Card", "Lista grande", "Grade", "Só texto", "Mini capa", "Expandido", "Minimal")
            android.app.AlertDialog.Builder(requireContext())
                .setTitle("Modo de visualização")
                .setSingleChoiceItems(labels, cur) { _, which ->
                    currentView = modes[which]
                    prefs?.edit()?.putString("view_mode", currentView.name)?.apply()
                    btnViewMode.text = when (currentView) {
                        ViewMode.DETAILED -> "Lista"
                        ViewMode.COMPACT -> "Comp."
                        ViewMode.CARD -> "Card"
                        ViewMode.LIST_LARGE -> "Gde."
                        ViewMode.GRID -> "Grade"
                        ViewMode.TEXT_ONLY -> "Texto"
                        ViewMode.COVER_SMALL -> "Mini"
                        ViewMode.EXPANDED -> "Exp."
                        ViewMode.MINIMAL -> "Min."
                    }
                    adapter.viewMode = currentView
                    if (currentView == ViewMode.GRID) {
                        recyclerView.layoutManager = GridLayoutManager(requireContext(), 2)
                    } else {
                        recyclerView.layoutManager = LinearLayoutManager(requireContext())
                    }
                }
                .setPositiveButton("OK", null)
                .show()
        }

        btnMultiSelect.setOnClickListener {
            adapter.toggleMultiSelect()
            val ms = adapter.multiSelectMode
            btnMultiSelect.text = if (ms) "Canc." else "Sel."
            btnMultiSelect.setBackgroundResource(
                if (ms) R.drawable.btn_filter_active else R.drawable.btn_filter_inactive
            )
            btnAddSelected.visibility = if (ms && adapter.selectedSongs.isNotEmpty()) View.VISIBLE else View.GONE
        }

        btnAddSelected.setOnClickListener {
            val mp = (activity as? MainActivity)?.playerService?.musicPlayer
            val selected = adapter.selectedSongs.toList()
            if (mp != null && selected.isNotEmpty()) {
                selected.forEach { mp.addToQueue(it) }
                Toast.makeText(context, "${selected.size} música(s) adicionada(s) à fila", Toast.LENGTH_SHORT).show()
                exitMultiSelect()
            }
        }

        swipeRefresh.setOnRefreshListener {
            val act = activity as? MainActivity
            if (act != null && act.hasRequiredPermission()) {
                act.loadSongs()
            }
            swipeRefresh.isRefreshing = false
        }

        btnSort.text = sortLabels[currentSort]
        btnViewMode.text = when (currentView) {
            ViewMode.DETAILED -> "Lista"
            ViewMode.COMPACT -> "Comp."
            ViewMode.CARD -> "Card"
            ViewMode.LIST_LARGE -> "Gde."
            ViewMode.GRID -> "Grade"
            ViewMode.TEXT_ONLY -> "Texto"
            ViewMode.COVER_SMALL -> "Mini"
            ViewMode.EXPANDED -> "Exp."
            ViewMode.MINIMAL -> "Min."
        }
        if (currentView == ViewMode.GRID) {
            recyclerView.layoutManager = GridLayoutManager(requireContext(), 2)
        }

        return v
    }

    override fun onDestroyView() {
        super.onDestroyView()
        filterJob?.cancel()
        adapter.cleanup()
    }

    private fun exitMultiSelect() {
        if (adapter.multiSelectMode) adapter.toggleMultiSelect()
        btnMultiSelect.text = "Sel."
        btnMultiSelect.setBackgroundResource(R.drawable.btn_filter_inactive)
        btnAddSelected.visibility = View.GONE
    }

    private fun applyFilter() {
        filterJob?.cancel()
        filterJob = CoroutineScope(Dispatchers.Main).launch {
            val repo = repository ?: return@launch
            val allFavPaths = withContext(Dispatchers.IO) {
                repo.getAllFavorites().first().map { it.songPath }.toMutableSet()
            }
            adapter.favoritePaths = allFavPaths

            val playCounts = if (currentSort == SortMode.PLAY_COUNT) {
                val act = activity as? MainActivity
                act?.playCountManager?.getPlayCounts() ?: emptyMap()
            } else emptyMap()
            val sorted = SongAdapter.sortSongs(allSongs, currentSort, playCounts)
            val filtered = if (showFavoritesOnly) {
                sorted.filter { it.path in allFavPaths }
            } else {
                sorted
            }
            if (::adapter.isInitialized) {
                adapter.updateSongs(filtered)
                tvEmpty.visibility = if (filtered.isEmpty()) View.VISIBLE else View.GONE
                scrollToCurrentSong()
            }
        }
    }
}
