package com.mp3player.data.audio

import android.util.Log
import androidx.media3.common.audio.AudioProcessor
import androidx.media3.common.util.UnstableApi
import java.nio.ByteBuffer
import java.nio.ByteOrder

@UnstableApi
class EqualizerAudioProcessor : AudioProcessor {

    val bandsCount = 20
    val bands = mutableListOf<EqualizerBandState>()
    private val filters = Array(bandsCount) { BiquadFilter() }
    var preampGainDb: Float = 0f
        private set

    private var sampleRate = 44100
    private var channelCount = 2

    @Volatile
    private var isActiveState = false

    @Volatile
    var enabled = true
        private set

    private var inputEnded = false
    private var outputBuffer: ByteBuffer = ByteBuffer.allocate(0)
    private var cachedOutput = ShortArray(0)
    private var cachedOutBuf = ByteBuffer.allocate(0).order(ByteOrder.nativeOrder())

    // Peak limiter state
    @Volatile
    private var limiterGainReduction = 1f
    private var processedSamples = FloatArray(0)
    private val attackAlpha = 0.022f
    private val releaseAlpha = 0.00023f

    private val freqs = floatArrayOf(
        31f, 44f, 63f, 88f, 125f,
        175f, 250f, 350f, 500f, 700f,
        1000f, 1400f, 2000f, 2800f, 4000f,
        5600f, 8000f, 11200f, 16000f, 22000f
    )

    init {
        for (i in 0 until bandsCount) {
            bands.add(EqualizerBandState(i, freqs[i], 0f))
        }
    }

    fun setEnabled(on: Boolean) {
        enabled = on
        updateActiveState()
    }

    val gainReductionDb: Float
        get() {
            val gr = limiterGainReduction
            return if (gr >= 1f) 0f else (20.0 * Math.log10(gr.toDouble())).toFloat()
        }

    private fun updateActiveState() {
        isActiveState = enabled && (preampGainDb != 0f || bands.any { it.gainDb != 0f })
    }

    fun setBandGain(bandId: Int, gainDb: Float) {
        if (bandId in 0 until bandsCount) {
            bands[bandId].gainDb = gainDb
            filters[bandId].configure(bands[bandId].frequency, gainDb, sampleRate)
            updateActiveState()
        }
    }

    fun setPreampGain(gainDb: Float) {
        preampGainDb = gainDb
        updateActiveState()
    }

    fun resetAllBands() {
        for (i in 0 until bandsCount) {
            bands[i].gainDb = 0f
            filters[i].configure(bands[i].frequency, 0f, sampleRate)
            filters[i].reset()
        }
        preampGainDb = 0f
        updateActiveState()
    }

    fun applyPreset(gains: FloatArray, preamp: Float = 0f) {
        for (i in 0 until bandsCount.coerceAtMost(gains.size)) {
            bands[i].gainDb = gains[i]
            filters[i].configure(bands[i].frequency, gains[i], sampleRate)
        }
        preampGainDb = preamp
        updateActiveState()
    }

    fun getBandGain(bandId: Int): Float {
        return if (bandId in 0 until bandsCount) bands[bandId].gainDb else 0f
    }

    val allGains: FloatArray
        get() = FloatArray(bandsCount) { bands[it].gainDb }

    override fun configure(format: AudioProcessor.AudioFormat): AudioProcessor.AudioFormat {
        sampleRate = format.sampleRate
        channelCount = format.channelCount
        inputEnded = false
        for (i in 0 until bandsCount) {
            filters[i].configure(bands[i].frequency, bands[i].gainDb, sampleRate)
        }
        updateActiveState()
        return format
    }

    override fun isActive(): Boolean = true

    override fun queueInput(inputBuffer: ByteBuffer) {
        try {
            val remaining = inputBuffer.remaining() / 2
            if (remaining == 0) return

            // Bypass mode: passthrough audio unmodified
            if (!isActiveState) {
                val size = inputBuffer.limit()
                inputBuffer.position(size)
                inputBuffer.position(0)
                if (cachedOutBuf.capacity() < size) {
                    cachedOutBuf = ByteBuffer.allocate(size).order(inputBuffer.order())
                }
                cachedOutBuf.clear()
                cachedOutBuf.limit(size)
                cachedOutBuf.put(inputBuffer)
                cachedOutBuf.rewind()
                outputBuffer = cachedOutBuf
                inputEnded = false
                return
            }

            val input = inputBuffer.asShortBuffer()
            val preampLinear = Math.pow(10.0, (preampGainDb / 20.0)).toFloat()

            // Ensure temporary buffers are large enough
            if (cachedOutput.size < remaining) {
                cachedOutput = ShortArray(remaining)
            }
            if (processedSamples.size < remaining) {
                processedSamples = FloatArray(remaining)
            }
            val output = cachedOutput
            val samples = processedSamples

            // Step 1: Process through filter cascade + preamp into float array
            var peak = 0f
            for (i in 0 until remaining) {
                var sample = input[i].toFloat() / 32768f
                for (f in filters) {
                    sample = f.process(sample)
                }
                sample *= preampLinear
                samples[i] = sample
                val abs = if (sample >= 0f) sample else -sample
                if (abs > peak) peak = abs
            }

            // Step 2: Peak limiter with per-sample attack/release smoothing
            if (peak > 1.0f) {
                val targetGR = 1.0f / peak
                for (i in 0 until remaining) {
                    val coeff = if (targetGR < limiterGainReduction) attackAlpha else releaseAlpha
                    limiterGainReduction += (targetGR - limiterGainReduction) * coeff
                    samples[i] *= limiterGainReduction
                }
            } else {
                // Release back to unity
                val targetGR = 1.0f
                for (i in 0 until remaining) {
                    val coeff = if (targetGR < limiterGainReduction) attackAlpha else releaseAlpha
                    limiterGainReduction += (targetGR - limiterGainReduction) * coeff
                    samples[i] *= limiterGainReduction
                }
            }

            // Step 3: Soft-clip safety net + convert to shorts
            for (i in 0 until remaining) {
                output[i] = (Math.tanh(samples[i].toDouble()) * 32767f).toInt().toShort()
            }

            inputBuffer.position(inputBuffer.limit())

            if (cachedOutBuf.capacity() < remaining * 2) {
                cachedOutBuf = ByteBuffer.allocate(remaining * 2).order(ByteOrder.nativeOrder())
            }
            cachedOutBuf.clear()
            cachedOutBuf.limit(remaining * 2)
            cachedOutBuf.asShortBuffer().put(output, 0, remaining)
            cachedOutBuf.rewind()
            outputBuffer = cachedOutBuf
            inputEnded = false
        } catch (e: Exception) {
            Log.e("EqualizerAudioProcessor", "queueInput error", e)
            inputBuffer.position(inputBuffer.limit())
            inputEnded = false
        }
    }

    override fun getOutput(): ByteBuffer {
        val buf = outputBuffer
        outputBuffer = ByteBuffer.allocate(0)
        return buf
    }

    override fun isEnded(): Boolean = inputEnded

    override fun queueEndOfStream() {
        inputEnded = true
    }

    override fun flush() {
        outputBuffer = ByteBuffer.allocate(0)
        inputEnded = false
        limiterGainReduction = 1f
        for (f in filters) f.reset()
    }

    override fun reset() {
        flush()
        updateActiveState()
    }

    data class EqualizerBandState(
        val id: Int,
        val frequency: Float,
        var gainDb: Float
    )
}
