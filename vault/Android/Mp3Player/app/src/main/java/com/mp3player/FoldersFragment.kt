package com.mp3player

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

class FoldersFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: FolderAdapter
    private lateinit var tvCurrentPath: TextView
    private var onFolderClick: ((FolderItem) -> Unit)? = null
    private var folders: List<FolderItem> = emptyList()
    private var pendingPath: String? = null

    fun setFolders(folders: List<FolderItem>, currentPath: String, onClick: (FolderItem) -> Unit) {
        this.folders = folders
        this.onFolderClick = onClick
        if (::tvCurrentPath.isInitialized) {
            tvCurrentPath.text = currentPath
            adapter.updateFolders(folders)
        } else {
            pendingPath = currentPath
        }
    }

    override fun onCreateView(inflater: LayoutInflater, c: ViewGroup?, b: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_folders, c, false)
        recyclerView = v.findViewById(R.id.recycler_folders)
        tvCurrentPath = v.findViewById(R.id.tv_current_path)
        pendingPath?.let { tvCurrentPath.text = it }
        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        adapter = FolderAdapter(folders) { item -> onFolderClick?.invoke(item) }
        recyclerView.adapter = adapter
        return v
    }
}
