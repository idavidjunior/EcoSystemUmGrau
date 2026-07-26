package com.mp3player.data

import android.content.Context
import android.content.SharedPreferences
import com.mp3player.MusicPlayer

object EqStateLoader {

    private const val PREFS_NAME = "eq_active_state"
    private const val KEY_VERSION = "format_version"
    private const val KEY_GAINS = "gains"
    private const val KEY_PREAMP = "preamp"
    private const val KEY_ENABLED = "eq_enabled"
    private const val FORMAT_VERSION = 2
    private const val BAND_COUNT = 20

    fun restoreTo(mp: MusicPlayer, context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val gainsStr = prefs.getString(KEY_GAINS, null) ?: return

        val version = prefs.getInt(KEY_VERSION, 1)
        val currentPreamp = prefs.getFloat(KEY_PREAMP, 0f)

        val rawParts = if (gainsStr.contains("|")) {
            gainsStr.split("\\|".toRegex())
        } else {
            gainsStr.split(",")
        }
        val parts: List<String>
        if (version < 2 && rawParts.size > BAND_COUNT + 5) {
            val fixed = mutableListOf<String>()
            for (j in rawParts.indices step 2) {
                val intPart = rawParts[j]
                val decPart = rawParts.getOrElse(j + 1) { "0" }
                fixed.add("$intPart.$decPart")
            }
            parts = fixed
        } else {
            parts = rawParts
        }

        for (i in 0 until minOf(parts.size, BAND_COUNT)) {
            var g = parts[i].toFloatOrNull() ?: continue
            if (version < 2) g -= currentPreamp
            mp.setEqBandGain(i, g.coerceIn(-15f, 15f))
        }
        mp.setEqPreampGain(currentPreamp)

        val enabled = prefs.getBoolean(KEY_ENABLED, true)
        mp.equalizerProcessor?.setEnabled(enabled)
    }
}
