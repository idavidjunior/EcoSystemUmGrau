package com.mp3player

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

class ArtistDetailFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: SongAdapter
    private lateinit var tvArtistName: TextView
    private lateinit var tvArtistInfo: TextView
    private var songs: List<Song> = emptyList()
    private var onPlay: ((Song) -> Unit)? = null

    fun setArtist(name: String, albumCount: Int, songList: List<Song>, onPlaySong: (Song) -> Unit) {
        songs = songList
        onPlay = onPlaySong
        if (::adapter.isInitialized) {
            adapter.updateSongs(songs)
            tvArtistName.text = name
            tvArtistInfo.text = "$albumCount álbuns · ${songs.size} músicas"
        }
    }

    override fun onCreateView(inflater: LayoutInflater, c: ViewGroup?, b: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_artist_detail, c, false)
        recyclerView = v.findViewById(R.id.recycler_artist_songs)
        tvArtistName = v.findViewById(R.id.tv_artist_detail_name)
        tvArtistInfo = v.findViewById(R.id.tv_artist_detail_info)
        recyclerView.layoutManager = LinearLayoutManager(requireContext())

        val first = songs.firstOrNull()
        val albumCount = songs.distinctBy { it.album }.size
        tvArtistName.text = first?.artist ?: ""
        tvArtistInfo.text = "$albumCount álbuns · ${songs.size} músicas"

        adapter = SongAdapter(songs) { song -> onPlay?.invoke(song) }
        adapter.onEditTag = { song ->
            (activity as? MainActivity)?.openTagEditor(song)
        }
        recyclerView.adapter = adapter

        v.findViewById<View>(R.id.btn_back_artist).setOnClickListener {
            parentFragmentManager.popBackStack()
        }
        return v
    }

    override fun onDestroyView() {
        super.onDestroyView()
        adapter.cleanup()
    }
}
