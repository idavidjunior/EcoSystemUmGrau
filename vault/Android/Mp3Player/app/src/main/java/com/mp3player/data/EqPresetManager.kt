package com.mp3player.data

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject

data class EqPreset(
    val name: String,
    val gains: FloatArray,
    val preamp: Float = 0f,
    val isBuiltIn: Boolean = false
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is EqPreset) return false
        return name == other.name && gains.contentEquals(other.gains) && preamp == other.preamp
    }
    override fun hashCode(): Int = name.hashCode() * 31 + gains.contentHashCode() + preamp.hashCode()
}

class EqPresetManager(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences("eq_presets", Context.MODE_PRIVATE)

    fun loadCustomPresets(): MutableList<EqPreset> {
        val list = mutableListOf<EqPreset>()
        val json = prefs.getString("custom_presets", "[]") ?: "[]"
        try {
            val arr = JSONArray(json)
            for (i in 0 until arr.length()) {
                val obj = arr.getJSONObject(i)
                val name = obj.getString("name")
                val gainsArr = obj.getJSONArray("gains")
                val gains = FloatArray(gainsArr.length()) { gainsArr.getDouble(it).toFloat() }
                val preamp = obj.optDouble("preamp", 0.0).toFloat()
                list.add(EqPreset(name, gains, preamp, false))
            }
        } catch (_: Exception) {}
        return list
    }

    fun saveCustomPresets(presets: List<EqPreset>) {
        val arr = JSONArray()
        for (p in presets) {
            val gainsArr = JSONArray()
            for (g in p.gains) gainsArr.put(g.toDouble())
            arr.put(JSONObject()
                .put("name", p.name)
                .put("gains", gainsArr)
                .put("preamp", p.preamp.toDouble()))
        }
        prefs.edit().putString("custom_presets", arr.toString()).apply()
    }

    fun addOrUpdatePreset(preset: EqPreset) {
        val presets = loadCustomPresets()
        val idx = presets.indexOfFirst { it.name == preset.name }
        if (idx >= 0) presets[idx] = preset
        else presets.add(preset)
        saveCustomPresets(presets)
    }

    fun deletePreset(name: String) {
        val presets = loadCustomPresets()
        presets.removeAll { it.name == name }
        saveCustomPresets(presets)
    }
}
