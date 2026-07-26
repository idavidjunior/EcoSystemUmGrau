package com.mp3player.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import android.widget.Button
import android.widget.ImageButton
import android.widget.ListView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.mp3player.MainActivity
import com.mp3player.R
import com.mp3player.Song

class QueueBottomSheet : BottomSheetDialogFragment() {

    private lateinit var listView: ListView
    private lateinit var btnClear: Button
    private lateinit var tvEmpty: TextView
    private val adapter = QueueAdapter()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val v = inflater.inflate(R.layout.bottom_sheet_queue, container, false)
        listView = v.findViewById(R.id.queue_list)
        btnClear = v.findViewById(R.id.btn_clear_queue)
        tvEmpty = v.findViewById(R.id.tv_queue_empty)

        listView.adapter = adapter
        refreshQueue()

        btnClear.setOnClickListener {
            val mp = getMusicPlayer()
            if (mp?.getQueue()?.isNotEmpty() == true) {
                AlertDialog.Builder(requireContext())
                    .setTitle("Limpar fila")
                    .setMessage("Remover todas as musicas da fila?")
                    .setPositiveButton("Sim") { _, _ ->
                        mp.clearQueue()
                        refreshQueue()
                        Toast.makeText(context, "Fila limpa", Toast.LENGTH_SHORT).show()
                    }
                    .setNegativeButton("Nao", null)
                    .show()
            }
        }

        listView.setOnItemLongClickListener { _, _, position, _ ->
            val mp = getMusicPlayer()
            val queue = mp?.getQueue() ?: return@setOnItemLongClickListener true
            if (position in queue.indices) {
                val song = queue[position]
                AlertDialog.Builder(requireContext())
                    .setTitle("Remover da fila")
                    .setMessage("Remover \"${song.title}\"?")
                    .setPositiveButton("Remover") { _, _ ->
                        mp.removeFromQueue(position)
                        refreshQueue()
                    }
                    .setNegativeButton("Cancelar", null)
                    .show()
            }
            true
        }

        return v
    }

    private fun refreshQueue() {
        val mp = getMusicPlayer()
        val queue = mp?.getQueue() ?: emptyList()
        adapter.update(queue)
        tvEmpty.visibility = if (queue.isEmpty()) View.VISIBLE else View.GONE
    }

    private fun getMusicPlayer(): com.mp3player.MusicPlayer? {
        return (activity as? MainActivity)?.playerService?.musicPlayer
    }

    inner class QueueAdapter : BaseAdapter() {
        private val items = mutableListOf<Song>()

        fun update(newItems: List<Song>) {
            items.clear()
            items.addAll(newItems)
            notifyDataSetChanged()
        }

        override fun getCount(): Int = items.size
        override fun getItem(i: Int): Any = items[i]
        override fun getItemId(i: Int): Long = i.toLong()

        override fun getView(position: Int, convertView: View?, parent: ViewGroup?): View {
            val v = convertView ?: LayoutInflater.from(context).inflate(
                android.R.layout.simple_list_item_2, parent, false
            )
            val song = items[position]
            v.findViewById<TextView>(android.R.id.text1).text = song.title
            v.findViewById<TextView>(android.R.id.text2).text = song.artist
            return v
        }
    }
}
