package com.mp3player

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.mp3player.data.AlbumArtProvider
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class AlbumItem(val name: String, val artist: String, val songCount: Int, val songs: List<Song>)

class AlbumAdapter(
    private var albums: List<AlbumItem>,
    private val onItemClick: (AlbumItem) -> Unit
) : RecyclerView.Adapter<AlbumAdapter.ViewHolder>() {

    private val scope = CoroutineScope(Dispatchers.Main + Job())

    fun updateAlbums(new: List<AlbumItem>) {
        albums = new
        notifyDataSetChanged()
    }

    fun cleanup() { scope.cancel() }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val v = LayoutInflater.from(parent.context).inflate(R.layout.item_album, parent, false)
        return ViewHolder(v)
    }

    override fun onBindViewHolder(h: ViewHolder, i: Int) {
        val a = albums[i]
        h.name.text = a.name
        h.artist.text = a.artist
        h.count.text = "${a.songCount} músicas"
        h.art.setImageResource(android.R.color.transparent)

        val firstSong = a.songs.firstOrNull()
        if (firstSong != null) {
            scope.launch {
                val bmp = withContext(Dispatchers.IO) {
                    AlbumArtProvider.getAlbumArt(firstSong.path, h.itemView.context)
                }
                if (bmp != null) h.art.setImageBitmap(bmp)
            }
        }

        h.itemView.setOnClickListener { onItemClick(a) }
    }

    override fun getItemCount() = albums.size

    class ViewHolder(v: View) : RecyclerView.ViewHolder(v) {
        val name: TextView = v.findViewById(R.id.tv_album_name)
        val artist: TextView = v.findViewById(R.id.tv_album_artist)
        val count: TextView = v.findViewById(R.id.tv_album_count)
        val art: ImageView = v.findViewById(R.id.iv_album_art)
    }
}
