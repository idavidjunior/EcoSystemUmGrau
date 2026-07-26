package com.mp3player

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

class AlbumsFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: AlbumAdapter
    private lateinit var tvEmpty: TextView
    private var onAlbumClick: ((AlbumItem) -> Unit)? = null
    private var pendingAlbums: List<AlbumItem>? = null

    fun setAlbums(albums: List<AlbumItem>, onClick: (AlbumItem) -> Unit) {
        this.onAlbumClick = onClick
        this.pendingAlbums = albums
        if (::adapter.isInitialized) {
            adapter.updateAlbums(albums)
            tvEmpty.visibility = if (albums.isEmpty()) View.VISIBLE else View.GONE
        }
    }

    override fun onCreateView(inflater: LayoutInflater, c: ViewGroup?, b: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_albums, c, false)
        recyclerView = v.findViewById(R.id.recycler_albums)
        tvEmpty = v.findViewById(R.id.tv_empty_albums)
        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        val items = pendingAlbums ?: emptyList()
        adapter = AlbumAdapter(items) { item ->
            onAlbumClick?.invoke(item)
        }
        recyclerView.adapter = adapter
        tvEmpty.visibility = if (items.isEmpty()) View.VISIBLE else View.GONE
        return v
    }

    override fun onDestroyView() {
        super.onDestroyView()
        if (::adapter.isInitialized) adapter.cleanup()
    }
}
