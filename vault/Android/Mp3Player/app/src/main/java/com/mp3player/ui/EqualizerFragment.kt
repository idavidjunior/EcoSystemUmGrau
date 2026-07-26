package com.mp3player.ui

import android.app.Dialog
import android.media.audiofx.Equalizer
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import java.util.Locale
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.SeekBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.DialogFragment
import com.mp3player.MainActivity
import com.mp3player.R
import com.mp3player.data.EqPreset
import com.mp3player.data.EqPresetManager

class EqualizerFragment : DialogFragment() {

    companion object {
        private const val BAND_COUNT = 20
        private const val PREFS_NAME = "eq_active_state"
        private const val KEY_VERSION = "format_version"
        private const val FORMAT_VERSION = 2
        private const val KEY_GAINS = "gains"
        private const val KEY_PREAMP = "preamp"
        private const val KEY_PRESET_IDX = "preset_idx"
        private const val KEY_PRESET_NAME = "preset_name"
        private const val KEY_ENABLED = "eq_enabled"

        private const val CUSTOM_IDX = -1

        private var savedEqualizer: Equalizer? = null
        private var savedSessionId = -1

        private fun fga(vararg values: Int): FloatArray = FloatArray(values.size) { values[it].toFloat() }

        private data class BuiltinPreset(val name: String, val gains: FloatArray, val preamp: Float = 0f)

        private val builtinPresets = listOf(
            BuiltinPreset("Flat", fga(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)),
            BuiltinPreset("Rock", fga(5,5,4,3,2,2,1,0,-1,-1,-1,0,1,2,3,4,5,5,6,6)),
            BuiltinPreset("Pop", fga(-1,0,2,3,4,4,3,2,1,0,0,0,-1,-1,0,1,2,3,3,4)),
            BuiltinPreset("Classical", fga(0,0,0,0,-1,-1,-2,-2,-2,-1,0,1,2,3,4,4,5,5,5,5)),
            BuiltinPreset("Jazz", fga(3,3,2,2,1,1,0,0,-1,-1,0,1,2,2,3,3,4,4,3,3)),
            BuiltinPreset("Dance", fga(6,6,5,5,4,3,2,1,0,-1,-2,-2,-1,0,2,3,4,5,5,5)),
            BuiltinPreset("Electronic", fga(6,5,5,4,3,2,1,0,-1,-2,-1,1,2,3,4,5,6,6,5,4)),
            BuiltinPreset("Hip-Hop", fga(7,7,6,5,4,3,2,1,0,-1,-1,0,0,1,2,3,4,5,6,7)),
            BuiltinPreset("R&B", fga(4,4,3,3,2,1,0,-1,-1,0,1,2,3,3,4,4,4,3,2,2)),
            BuiltinPreset("Vocal", fga(-3,-2,-1,0,1,2,4,5,6,5,4,3,1,0,-1,-2,-3,-4,-5,-6)),
            BuiltinPreset("Acoustic", fga(3,3,2,2,1,1,0,0,0,1,2,2,3,3,4,4,3,2,1,0)),
            BuiltinPreset("Soft", fga(-3,-2,-1,-1,0,0,1,1,1,1,0,0,-1,-1,-2,-2,-3,-3,-4,-5)),
            BuiltinPreset("Loudness", fga(8,7,6,5,4,3,2,1,0,0,0,0,1,2,3,4,5,6,7,8)),
            BuiltinPreset("Bass Boost", fga(8,8,8,7,7,6,5,4,3,2,1,0,-1,-2,-3,-3,-4,-4,-4,-4)),
            BuiltinPreset("Treble Boost", fga(-4,-4,-4,-3,-3,-2,-2,-1,0,1,2,3,4,5,6,7,8,8,8,8)),
        )
    }

    private var equalizer: Equalizer? = null
    private var presetManager: EqPresetManager? = null

    // Hardware range in millibels
    private var hwMinMb = -15000
    private var hwMaxMb = 15000

    // Cache em memória — UI sempre lê daqui, nunca do hardware
    private val currentGains = FloatArray(BAND_COUNT) { 0f }
    private var currentPreamp = 0f
    private var currentPresetIdx = CUSTOM_IDX
    private var currentPresetName = "Predefinições"

    private lateinit var bandsContainer: LinearLayout
    private lateinit var presetNameLabel: TextView
    private lateinit var preampValue: TextView
    private lateinit var preampSeek: SeekBar
    private lateinit var eqToggle: Button
    private lateinit var limiterIndicator: TextView
    private val limiterHandler = Handler(Looper.getMainLooper())
    private var restoringEqState = false
    private val limiterRunnable = object : Runnable {
        override fun run() {
            updateLimiterDisplay()
            limiterHandler.postDelayed(this, 250)
        }
    }

    private val virtualFrequencies = floatArrayOf(
        31f, 44f, 63f, 88f, 125f,
        175f, 250f, 350f, 500f, 700f,
        1000f, 1400f, 2000f, 2800f, 4000f,
        5600f, 8000f, 11200f, 16000f, 22000f
    )
    private val virtualToHw = IntArray(BAND_COUNT) { 0 }

    private val filePicker = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri != null) loadPresetFromFile(uri)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setStyle(STYLE_NO_FRAME, android.R.style.Theme_NoTitleBar_Fullscreen)
    }

    override fun onResume() {
        super.onResume()
        limiterHandler.post(limiterRunnable)
    }

    override fun onPause() {
        super.onPause()
        limiterHandler.removeCallbacks(limiterRunnable)
        saveActivePreset()
    }

    override fun onCreateDialog(savedInstanceState: Bundle?): Dialog {
        val dialog = super.onCreateDialog(savedInstanceState)
        dialog.window?.let { w ->
            w.setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
            w.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN)
            w.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND)
        }
        return dialog
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_equalizer, container, false)
        bandsContainer = v.findViewById(R.id.bands_container)
        presetNameLabel = v.findViewById(R.id.tv_preset_name)
        presetManager = EqPresetManager(requireContext())

        eqToggle = v.findViewById(R.id.btn_eq_toggle)
        limiterIndicator = v.findViewById(R.id.tv_limiter)

        eqToggle.setOnClickListener {
            if (!restoringEqState) toggleEq(!eqToggle.isSelected)
        }

        v.findViewById<Button>(R.id.btn_save_eq).setOnClickListener { showSaveDialog() }
        v.findViewById<Button>(R.id.btn_reset_eq).setOnClickListener { resetAllBands() }
        v.findViewById<Button>(R.id.btn_recarregar).setOnClickListener { filePicker.launch("application/json") }
        v.findViewById<View>(R.id.knob_presets_area).setOnClickListener { showPresetsDialog() }
        v.findViewById<View>(R.id.knob_presets_area).setOnLongClickListener { showCustomPresetsDialog(); true }
        v.findViewById<View>(R.id.btn_prev_preset).setOnClickListener { prevPreset() }
        v.findViewById<View>(R.id.btn_next_preset).setOnClickListener { nextPreset() }
        v.findViewById<View>(R.id.knob_volume_area).setOnClickListener { showVolumeDialog() }
        v.findViewById<View>(R.id.btn_close_eq)?.setOnClickListener { dismiss() }

        initEqualizer()
        return v
    }

    private fun toggleEq(on: Boolean) {
        eqToggle.isSelected = on
        eqToggle.text = if (on) "EQ ON" else "EQ OFF"
        eqToggle.setBackgroundResource(if (on) R.drawable.bg_preset_active else R.drawable.bg_preset_btn)
        eqToggle.setTextColor(if (on) 0xFF00BFFF.toInt() else 0xFFB0B0B0.toInt())
        equalizer?.setEnabled(on)
        getMusicPlayer()?.equalizerProcessor?.setEnabled(on)
        if (on) {
            for (i in currentGains.indices) {
                getMusicPlayer()?.setEqBandGain(i, currentGains[i])
            }
            getMusicPlayer()?.setEqPreampGain(currentPreamp)
        }
    }

    private fun updateLimiterDisplay() {
        val mp = getMusicPlayer()
        val reduction = mp?.equalizerProcessor?.gainReductionDb ?: 0f
        if (reduction < -0.5f) {
            limiterIndicator.text = "LIM: ${"%.1f".format(reduction)} dB"
            limiterIndicator.setTextColor(if (reduction < -3f) 0xFFFF5252.toInt() else 0xFFFFEB3B.toInt())
        } else {
            limiterIndicator.text = "LIM: 0.0 dB"
            limiterIndicator.setTextColor(0xFF66BB6A.toInt())
        }
    }

    private fun initEqualizer() {
        val act = activity as? MainActivity
        val sessionId = act?.playerService?.musicPlayer?.audioSessionId ?: 0
        if (sessionId == 0) {
            Handler(Looper.getMainLooper()).postDelayed({ initEqualizer() }, 500)
            return
        }
        if (savedEqualizer != null && savedSessionId == sessionId) {
            equalizer = savedEqualizer
            equalizer?.setEnabled(true)
        } else {
            try {
                savedEqualizer?.release()
                equalizer = Equalizer(0, sessionId).apply { setEnabled(true) }
                savedEqualizer = equalizer
                savedSessionId = sessionId
            } catch (e: Exception) {
                Toast.makeText(context, "Equalizador HW indisponivel: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
        equalizer?.let { eq ->
            val range = eq.bandLevelRange
            hwMinMb = range[0].toInt()
            hwMaxMb = range[1].toInt()
            buildBandMapping()
        }
        loadActivePreset()
        rebuildBands()
    }

    private fun buildBandMapping() {
        val hwCount = equalizer!!.numberOfBands.toInt()
        val hwFreqs = FloatArray(hwCount) { i -> equalizer!!.getCenterFreq(i.toShort()).toFloat() }
        for (v in virtualFrequencies.indices) {
            var best = 0
            var bestDist = Float.MAX_VALUE
            for (h in hwFreqs.indices) {
                val dist = kotlin.math.abs(virtualFrequencies[v] - hwFreqs[h])
                if (dist < bestDist) { bestDist = dist; best = h }
            }
            virtualToHw[v] = best
        }
    }

    // Conversão half-dB — round simétrico para evitar drift
    private fun gainToProgress(gainDb: Float): Int {
        val halfDbSteps = Math.round(gainDb / 0.5f)
        val range = (hwMaxMb - hwMinMb) / 100
        val centerSteps = range / 2 * 2
        return (halfDbSteps + centerSteps).coerceIn(0, range * 2)
    }

    private fun progressToGain(progress: Int): Float {
        val range = (hwMaxMb - hwMinMb) / 100
        val centerSteps = range / 2 * 2
        return ((progress - centerSteps) * 0.5f).coerceIn(hwMinMb / 100f, hwMaxMb / 100f)
    }

    private fun rebuildBands() {
        bandsContainer.removeAllViews()
        for (i in virtualFrequencies.indices) addBandRow(i)
    }

    private fun addBandRow(vIdx: Int) {
        val row = LinearLayout(requireContext())
        row.orientation = LinearLayout.HORIZONTAL
        row.gravity = Gravity.CENTER_VERTICAL
        val lp = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
        lp.setMargins(0, 1, 0, 1)
        row.layoutParams = lp

        val freq = virtualFrequencies[vIdx]
        val label = TextView(requireContext())
        label.text = if (freq >= 1000f) "%.0fK".format(freq / 1000f) else "%.0f".format(freq)
        label.setTextColor(0xFF999999.toInt())
        label.textSize = 10f
        label.typeface = android.graphics.Typeface.DEFAULT_BOLD
        label.gravity = Gravity.END or Gravity.CENTER_VERTICAL
        label.layoutParams = LinearLayout.LayoutParams(46, LinearLayout.LayoutParams.WRAP_CONTENT)
            .apply { setMargins(0, 0, 4, 0) }
        row.addView(label)

        val seek = SeekBar(requireContext(), null, android.R.attr.seekBarStyle)
        val rangeDb = (hwMaxMb - hwMinMb) / 100
        seek.max = rangeDb * 2
        seek.progress = gainToProgress(currentGains[vIdx])
        seek.layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        try { seek.progressDrawable = resources.getDrawable(R.drawable.seekbar_h_track, null) } catch (_: Exception) {}
        try { seek.thumb = resources.getDrawable(R.drawable.seekbar_h_thumb, null) } catch (_: Exception) {}
        row.addView(seek)

        val valueText = TextView(requireContext())
        valueText.text = formatGain(currentGains[vIdx])
        valueText.setTextColor(gainColor(currentGains[vIdx]))
        valueText.textSize = 10f
        valueText.typeface = android.graphics.Typeface.DEFAULT_BOLD
        valueText.gravity = Gravity.CENTER_VERTICAL
        valueText.layoutParams = LinearLayout.LayoutParams(40, LinearLayout.LayoutParams.WRAP_CONTENT)
            .apply { setMargins(4, 0, 0, 0) }
        row.addView(valueText)

        val hwIdx = virtualToHw[vIdx]
        seek.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(sb: SeekBar?, progress: Int, fromUser: Boolean) {
                if (!fromUser) return
                val g = progressToGain(progress)
                currentGains[vIdx] = g
                valueText.text = formatGain(g)
                valueText.setTextColor(gainColor(g))
                val effective = (g + currentPreamp).coerceIn(hwMinMb / 100f, hwMaxMb / 100f)
                val mb = (effective * 100).toInt().coerceIn(hwMinMb, hwMaxMb)
                equalizer?.setBandLevel(hwIdx.toShort(), mb.toShort())
                val mp = getMusicPlayer()
                mp?.setEqBandGain(vIdx, g)
                if (currentPresetIdx != CUSTOM_IDX) {
                    currentPresetIdx = CUSTOM_IDX
                    updatePresetNameDisplay("Customizado")
                }
                saveActivePreset()
            }
            override fun onStartTrackingTouch(sb: SeekBar?) {}
            override fun onStopTrackingTouch(sb: SeekBar?) {}
        })

        bandsContainer.addView(row)
    }

    private fun getMusicPlayer(): com.mp3player.MusicPlayer? =
        (activity as? com.mp3player.MainActivity)?.playerService?.musicPlayer

    private fun syncSoftwareEq() {
        val mp = getMusicPlayer() ?: return
        for (i in currentGains.indices) {
            mp.setEqBandGain(i, currentGains[i])
        }
        mp.setEqPreampGain(currentPreamp)
    }

    private fun formatGain(g: Float): String = if (g > 0) "+${"%.1f".format(g)}" else "%.1f".format(g)

    private fun gainColor(g: Float): Int = when {
        g > 0.1f -> 0xFF00E676.toInt()
        g < -0.1f -> 0xFFFF5252.toInt()
        else -> 0xFFB0B0B0.toInt()
    }

    private fun resetAllBands() {
        for (i in currentGains.indices) currentGains[i] = 0f
        currentPreamp = 0f
        val n = equalizer?.numberOfBands?.toInt() ?: 0
        for (h in 0 until n)
            equalizer?.setBandLevel(h.toShort(), 0.toShort())
        getMusicPlayer()?.resetEq()
        currentPresetIdx = CUSTOM_IDX
        updatePresetNameDisplay("Customizado")
        saveActivePreset()
        rebuildBands()
        Toast.makeText(context, "Equalizador reiniciado", Toast.LENGTH_SHORT).show()
    }

    private fun applyPreset(gains: FloatArray, preamp: Float, name: String) {
        currentPreamp = preamp
        val maxV = minOf(gains.size, currentGains.size)
        for (v in 0 until maxV) {
            val raw = gains[v].coerceIn(hwMinMb / 100f, hwMaxMb / 100f)
            currentGains[v] = raw
            if (equalizer != null) {
                val hw = virtualToHw[v]
                val effective = (raw + preamp).coerceIn(hwMinMb / 100f, hwMaxMb / 100f)
                equalizer!!.setBandLevel(hw.toShort(), (effective * 100).toInt().toShort())
            }
        }
        syncSoftwareEq()
        updatePresetNameDisplay(name)
        rebuildBands()
        saveActivePreset()
        Toast.makeText(context, name, Toast.LENGTH_SHORT).show()
    }

    private fun updatePresetNameDisplay(name: String) {
        currentPresetName = name
        if (::presetNameLabel.isInitialized) presetNameLabel.text = name
    }

    private fun applyPresetByIndex(idx: Int) {
        if (idx < 0 || idx >= builtinPresets.size) return
        currentPresetIdx = idx
        val p = builtinPresets[idx]
        applyPreset(p.gains, p.preamp, p.name)
    }

    private fun nextPreset() {
        var idx = currentPresetIdx
        if (idx == CUSTOM_IDX) idx = 0 else idx = (idx + 1) % builtinPresets.size
        applyPresetByIndex(idx)
    }

    private fun prevPreset() {
        var idx = currentPresetIdx
        if (idx == CUSTOM_IDX) idx = 0 else idx = if (idx == 0) builtinPresets.size - 1 else idx - 1
        applyPresetByIndex(idx)
    }

    private fun saveActivePreset() {
        val prefs = requireContext().getSharedPreferences(PREFS_NAME, android.content.Context.MODE_PRIVATE)
        val gainsStr = currentGains.joinToString("|") {
            java.lang.String.format(java.util.Locale.US, "%.1f", it)
        }
        prefs.edit()
            .putInt(KEY_VERSION, FORMAT_VERSION)
            .putString(KEY_GAINS, gainsStr)
            .putFloat(KEY_PREAMP, currentPreamp)
            .putInt(KEY_PRESET_IDX, currentPresetIdx)
            .putString(KEY_PRESET_NAME, currentPresetName)
            .putBoolean(KEY_ENABLED, eqToggle.isSelected)
            .apply()
    }

    private fun loadActivePreset() {
        val prefs = requireContext().getSharedPreferences(PREFS_NAME, android.content.Context.MODE_PRIVATE)
        val gainsStr = prefs.getString(KEY_GAINS, null)
        if (gainsStr == null) return
        val version = prefs.getInt(KEY_VERSION, 1)
        currentPreamp = prefs.getFloat(KEY_PREAMP, 0f)

        val rawParts = if (gainsStr.contains("|")) {
            gainsStr.split("\\|".toRegex())
        } else {
            gainsStr.split(",")
        }
        val parts: List<String>
        if (version < 2 && rawParts.size > BAND_COUNT + 5) {
            // Old format corrupted by locale decimal comma (pt_BR: -4,0 instead of -4.0)
            // Every pair of parts encodes one gain value
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

        for (i in 0 until minOf(parts.size, currentGains.size)) {
            var g = parts[i].toFloatOrNull() ?: continue
            if (version < 2) g -= currentPreamp
            currentGains[i] = g.coerceIn(hwMinMb / 100f, hwMaxMb / 100f)
            if (equalizer != null && i < virtualToHw.size) {
                val hw = virtualToHw[i]
                val effective = (g + currentPreamp).coerceIn(hwMinMb / 100f, hwMaxMb / 100f)
                equalizer?.setBandLevel(hw.toShort(), (effective * 100).toInt().toShort())
            }
        }
        currentPresetIdx = prefs.getInt(KEY_PRESET_IDX, CUSTOM_IDX)
        currentPresetName = prefs.getString(KEY_PRESET_NAME, "Predefinições") ?: "Predefinições"
        updatePresetNameDisplay(currentPresetName)
        syncSoftwareEq()
        val enabled = prefs.getBoolean(KEY_ENABLED, true)
        if (::eqToggle.isInitialized) {
            restoringEqState = true
            eqToggle.isSelected = enabled
            eqToggle.text = if (enabled) "EQ ON" else "EQ OFF"
            eqToggle.setBackgroundResource(if (enabled) R.drawable.bg_preset_active else R.drawable.bg_preset_btn)
            eqToggle.setTextColor(if (enabled) 0xFF00BFFF.toInt() else 0xFFB0B0B0.toInt())
            restoringEqState = false
        }
        equalizer?.setEnabled(enabled)
        getMusicPlayer()?.equalizerProcessor?.setEnabled(enabled)
    }

    private fun getCurrentGains(): FloatArray = currentGains.clone()

    private fun showPresetsDialog() {
        AlertDialog.Builder(requireContext())
            .setTitle("Predefinicoes")
            .setItems(builtinPresets.map { it.name }.toTypedArray()) { _, which ->
                applyPresetByIndex(which)
            }
            .setNeutralButton("Cancelar", null).show()
    }

    private fun showCustomPresetsDialog(): Boolean {
        val presets = presetManager?.loadCustomPresets() ?: return false
        if (presets.isEmpty()) { Toast.makeText(context, "Nenhum preset salvo", Toast.LENGTH_SHORT).show(); return false }
        AlertDialog.Builder(requireContext())
            .setTitle("Meus Presets")
            .setItems(presets.map { it.name }.toTypedArray()) { _, which ->
                currentPresetIdx = CUSTOM_IDX
                val p = presets[which]
                applyPreset(p.gains, p.preamp, p.name)
            }
            .setNeutralButton("Cancelar", null).show()
        return true
    }

    private fun showVolumeDialog() {
        val input = EditText(requireContext())
        input.setHint("Preamp (dB)")
        input.setText("%.1f".format(currentPreamp))
        input.inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                android.text.InputType.TYPE_NUMBER_FLAG_SIGNED or
                android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
        input.setTextColor(0xFFFFFFFF.toInt())
        input.setHintTextColor(0xFF888888.toInt())
        AlertDialog.Builder(requireContext())
            .setTitle("Pre-amplificador")
            .setView(input)
            .setPositiveButton("OK") { _, _ ->
                val v = input.text.toString().toFloatOrNull() ?: return@setPositiveButton
                currentPreamp = v
                for (i in virtualFrequencies.indices) {
                    val effective = (currentGains[i] + v).coerceIn(hwMinMb / 100f, hwMaxMb / 100f)
                    val hw = virtualToHw[i]
                    val mb = (effective * 100).toInt().toShort()
                    equalizer?.setBandLevel(hw.toShort(), mb.toShort())
                }
                syncSoftwareEq()
                saveActivePreset()
                Toast.makeText(context, "Preamp: ${"%.1f".format(v)} dB", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Cancelar", null).show()
    }

    private fun loadPresetFromFile(uri: Uri) {
        try {
            val input = requireContext().contentResolver.openInputStream(uri) ?: return
            val json = input.bufferedReader().use { it.readText() }
            val root = org.json.JSONObject(json)
            val gainsArr = root.getJSONArray("bands")
            val gains: FloatArray
            if (gainsArr.length() > 0 && gainsArr.get(0) is Number) {
                // Array de números simples
                gains = FloatArray(gainsArr.length()) { gainsArr.getDouble(it).toFloat() }
            } else {
                // Array de objetos {frequency, gain}
                gains = FloatArray(gainsArr.length()) { gainsArr.getJSONObject(it).getDouble("gain").toFloat() }
            }
            val preamp = root.optDouble("preamp", 0.0).toFloat()
            applyPreset(gains, preamp, root.optString("preset", root.optString("name", "Arquivo")))
        } catch (e: Exception) { Toast.makeText(context, "Erro ao carregar arquivo", Toast.LENGTH_SHORT).show() }
    }

    private fun showSaveDialog() {
        val gains = getCurrentGains()
        val input = EditText(requireContext())
        input.setHint("Nome do preset")
        input.setTextColor(0xFFFFFFFF.toInt())
        input.setHintTextColor(0xFF888888.toInt())
        AlertDialog.Builder(requireContext())
            .setTitle("Salvar como Preset")
            .setView(input)
            .setPositiveButton("Salvar") { _, _ ->
                val name = input.text.toString().trim()
                if (name.isEmpty()) { Toast.makeText(context, "Nome invalido", Toast.LENGTH_SHORT).show(); return@setPositiveButton }
                presetManager?.addOrUpdatePreset(EqPreset(name, gains, currentPreamp))
                Toast.makeText(context, "Preset \"$name\" salvo", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Cancelar", null).show()
    }

    override fun onDestroy() {
        super.onDestroy()
        // savedEqualizer is a static cache shared across instances.
        // It is properly released in initEqualizer() when the session changes.
        // Do NOT release here — it would break the cache for config changes.
    }

}
