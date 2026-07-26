package com.mp3player

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

class AlbumDetailFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: SongAdapter
    private lateinit var tvAlbumName: TextView
    private lateinit var tvAlbumInfo: TextView
    private var songs: List<Song> = emptyList()
    private var albumName: String = ""
    private var artistName: String = ""
    private var onPlay: ((Song) -> Unit)? = null
    private var pendingSongs: List<Song>? = null
    private var pendingAlbumName: String? = null
    private var pendingArtistName: String? = null

    fun setAlbum(name: String, artist: String, songList: List<Song>, onPlaySong: (Song) -> Unit) {
        albumName = name
        artistName = artist
        songs = songList
        onPlay = onPlaySong
        pendingAlbumName = name
        pendingArtistName = artist
        pendingSongs = songList
        if (::adapter.isInitialized) {
            adapter.updateSongs(songs)
            tvAlbumName.text = name
            tvAlbumInfo.text = "$artist · ${songs.size} músicas"
        }
    }

    override fun onCreateView(inflater: LayoutInflater, c: ViewGroup?, b: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_album_detail, c, false)
        recyclerView = v.findViewById(R.id.recycler_album_songs)
        tvAlbumName = v.findViewById(R.id.tv_album_detail_name)
        tvAlbumInfo = v.findViewById(R.id.tv_album_detail_info)
        recyclerView.layoutManager = LinearLayoutManager(requireContext())

        val name = pendingAlbumName ?: albumName
        val artist = pendingArtistName ?: ""
        val list = pendingSongs ?: songs

        tvAlbumName.text = name
        val first = list.firstOrNull()
        tvAlbumInfo.text = "${artist.ifEmpty { first?.artist ?: "" }} · ${list.size} músicas"

        adapter = SongAdapter(list) { song -> onPlay?.invoke(song) }
        adapter.onEditTag = { song ->
            (activity as? MainActivity)?.openTagEditor(song)
        }
        recyclerView.adapter = adapter

        v.findViewById<View>(R.id.btn_back_album).setOnClickListener {
            parentFragmentManager.popBackStack()
        }
        return v
    }

    override fun onDestroyView() {
        super.onDestroyView()
        adapter.cleanup()
    }
}
