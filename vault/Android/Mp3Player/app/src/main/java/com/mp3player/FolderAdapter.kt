package com.mp3player

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

data class FolderItem(val path: String, val name: String, val songCount: Int, val songs: List<Song>)

class FolderAdapter(
    private var folders: List<FolderItem>,
    private val onItemClick: (FolderItem) -> Unit
) : RecyclerView.Adapter<FolderAdapter.ViewHolder>() {

    fun updateFolders(new: List<FolderItem>) {
        folders = new
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val v = LayoutInflater.from(parent.context).inflate(R.layout.item_folder, parent, false)
        return ViewHolder(v)
    }

    override fun onBindViewHolder(h: ViewHolder, i: Int) {
        val f = folders[i]
        h.name.text = f.name
        h.path.text = f.path
        h.count.text = "${f.songCount} músicas"
        h.itemView.setOnClickListener { onItemClick(f) }
    }

    override fun getItemCount() = folders.size

    class ViewHolder(v: View) : RecyclerView.ViewHolder(v) {
        val name: TextView = v.findViewById(R.id.tv_folder_name)
        val path: TextView = v.findViewById(R.id.tv_folder_path)
        val count: TextView = v.findViewById(R.id.tv_folder_count)
    }
}
