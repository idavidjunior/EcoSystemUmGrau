package com.mp3player.data.audio

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

class BiquadFilter {

    private var b0 = 0.0; private var b1 = 0.0; private var b2 = 0.0
    private var a1 = 0.0; private var a2 = 0.0

    private var x1 = 0.0; private var x2 = 0.0
    private var y1 = 0.0; private var y2 = 0.0

    fun configure(frequencyHz: Float, gainDb: Float, sampleRate: Int) {
        if (gainDb == 0f) {
            b0 = 1.0; b1 = 0.0; b2 = 0.0
            a1 = 0.0; a2 = 0.0
            return
        }
        val w0 = 2.0 * PI * frequencyHz / sampleRate
        val a = 10.0.pow(gainDb / 40.0)
        val alpha = sin(w0) / (2.0 * Q)
        val cosW0 = cos(w0)

        b0 = 1.0 + alpha * a
        b1 = -2.0 * cosW0
        b2 = 1.0 - alpha * a
        val a0 = 1.0 + alpha / a
        a1 = -2.0 * cosW0
        a2 = 1.0 - alpha / a

        b0 /= a0; b1 /= a0; b2 /= a0
        a1 /= a0; a2 /= a0

        x1 = 0.0; x2 = 0.0; y1 = 0.0; y2 = 0.0
    }

    fun process(sample: Float): Float {
        val x = sample.toDouble()
        val y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2 = x1; x1 = x
        y2 = y1; y1 = y
        return y.toFloat()
    }

    fun reset() {
        x1 = 0.0; x2 = 0.0; y1 = 0.0; y2 = 0.0
    }

    companion object {
        private const val Q = 0.707
    }
}
