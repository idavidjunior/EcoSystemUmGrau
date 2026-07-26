package com.mp3player

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

class ArtistsFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: ArtistAdapter
    private lateinit var tvEmpty: TextView
    private var onArtistClick: ((ArtistItem) -> Unit)? = null
    private var pendingArtists: List<ArtistItem>? = null

    fun setArtists(artists: List<ArtistItem>, onClick: (ArtistItem) -> Unit) {
        this.onArtistClick = onClick
        this.pendingArtists = artists
        if (::adapter.isInitialized) {
            adapter.updateArtists(artists)
            tvEmpty.visibility = if (artists.isEmpty()) View.VISIBLE else View.GONE
        }
    }

    override fun onCreateView(inflater: LayoutInflater, c: ViewGroup?, b: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_artists, c, false)
        recyclerView = v.findViewById(R.id.recycler_artists)
        tvEmpty = v.findViewById(R.id.tv_empty_artists)
        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        val items = pendingArtists ?: emptyList()
        adapter = ArtistAdapter(items) { item ->
            onArtistClick?.invoke(item)
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
