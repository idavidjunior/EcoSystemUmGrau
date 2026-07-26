package com.mp3player.data.model

data class EqualizerBand(
    val id: Int,
    val centerFrequencyHz: Float,
    var gainDb: Float = 0f
) {
    val label: String
        get() = if (centerFrequencyHz >= 1000f)
            "%.1fk".format(centerFrequencyHz / 1000f)
        else
            "%.0f".format(centerFrequencyHz)

    companion object {
        val FREQUENCIES = floatArrayOf(
            31f, 44f, 63f, 88f, 125f, 175f, 250f, 350f, 500f, 700f,
            1000f, 1400f, 2000f, 2800f, 4000f, 5600f, 8000f, 11200f, 16000f, 20000f
        )

        fun createDefaultBands(): List<EqualizerBand> =
            FREQUENCIES.mapIndexed { index, freq -> EqualizerBand(index, freq) }
    }
}
