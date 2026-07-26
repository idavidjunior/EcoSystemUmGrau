package com.mp3player.data

import android.content.Context
import org.json.JSONObject

class PlayCountManager(context: Context) {

    private val prefs = context.getSharedPreferences("play_counts", Context.MODE_PRIVATE)

    fun getPlayCounts(): Map<String, Int> {
        val json = prefs.getString("counts", "{}") ?: "{}"
        val map = mutableMapOf<String, Int>()
        try {
            val obj = JSONObject(json)
            for (key in obj.keys()) {
                map[key] = obj.getInt(key)
            }
        } catch (_: Exception) {}
        return map
    }

    fun getCount(path: String): Int = getPlayCounts()[path] ?: 0

    fun incrementPlayCount(path: String) {
        val counts = getPlayCounts().toMutableMap()
        counts[path] = (counts[path] ?: 0) + 1
        prefs.edit().putString("counts", JSONObject(counts.toMap()).toString()).apply()
    }
}
