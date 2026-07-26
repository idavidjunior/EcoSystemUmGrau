package com.mp3player.data.audio

object EqualizerPresets {

    data class Preset(val name: String, val gains: FloatArray) {
        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (other !is Preset) return false
            return name == other.name && gains.contentEquals(other.gains)
        }
        override fun hashCode(): Int = name.hashCode() * 31 + gains.contentHashCode()
    }

    val presets = listOf(
        Preset("Flat", floatArrayOf(0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f)),
        Preset("Pop", floatArrayOf(0f,0f,2f,1f,3f,4f,5f,4f,3f,2f,3f,4f,5f,4f,3f,2f,2f,1f,1f,0f)),
        Preset("Rock", floatArrayOf(3f,3f,4f,3f,2f,1f,0f,0f,1f,2f,3f,3f,4f,5f,5f,4f,3f,2f,1f,0f)),
        Preset("Jazz", floatArrayOf(2f,2f,3f,4f,4f,3f,2f,1f,2f,3f,4f,4f,3f,3f,4f,5f,4f,3f,2f,0f)),
        Preset("Clássica", floatArrayOf(4f,4f,3f,2f,1f,0f,0f,0f,0f,0f,1f,2f,3f,4f,4f,3f,2f,1f,0f,0f)),
        Preset("Dance", floatArrayOf(4f,4f,5f,4f,3f,2f,1f,0f,0f,1f,2f,3f,4f,5f,5f,4f,3f,2f,1f,0f)),
        Preset("Voz", floatArrayOf(0f,0f,0f,0f,0f,0f,1f,2f,3f,4f,5f,4f,3f,2f,1f,0f,0f,0f,0f,0f)),
        Preset("Acústico", floatArrayOf(2f,2f,3f,4f,4f,3f,2f,1f,0f,0f,1f,2f,3f,4f,4f,3f,2f,1f,0f,0f)),
        Preset("Bass Boost", floatArrayOf(6f,6f,5f,4f,3f,2f,1f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f,0f)),
    )
}
