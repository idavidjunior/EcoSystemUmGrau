package com.mp3player.data.online

import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.ShortBuffer

object AudioDecoder {

    private const val TARGET_SAMPLE_RATE = 11025
    private const val TARGET_CHANNELS = 1
    private const val MAX_DECODE_SECONDS = 60

    data class DecodeResult(
        val pcm: ByteArray,
        val sampleRate: Int,
        val channels: Int,
        val durationSeconds: Float
    )

    fun decodeToPcm(filePath: String): DecodeResult? {
        val extractor = MediaExtractor()
        return try {
            extractor.setDataSource(filePath)

            val trackIndex = selectAudioTrack(extractor) ?: return null

            extractor.selectTrack(trackIndex)
            val format = extractor.getTrackFormat(trackIndex)
            val mime = format.getString(MediaFormat.KEY_MIME) ?: return null

            val codec = MediaCodec.createDecoderByType(mime)
            val outputBuffers = mutableListOf<ByteArray>()
            var totalSamples = 0L
            var inputDone = false
            var outputDone = false

            val maxInputSamples = MAX_DECODE_SECONDS * TARGET_SAMPLE_RATE * TARGET_CHANNELS

            codec.configure(format, null, null, 0)
            codec.start()

            val bufferInfo = MediaCodec.BufferInfo()
            val timeoutUs = 10000L

            while (!outputDone) {
                if (!inputDone) {
                    val inputIndex = codec.dequeueInputBuffer(timeoutUs)
                    if (inputIndex >= 0) {
                        val inputBuf = codec.getInputBuffer(inputIndex)!!
                        val sampleSize = extractor.readSampleData(inputBuf, 0)
                        if (sampleSize < 0) {
                            codec.queueInputBuffer(inputIndex, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM)
                            inputDone = true
                        } else {
                            val pts = extractor.sampleTime
                            codec.queueInputBuffer(inputIndex, 0, sampleSize, pts, 0)
                            extractor.advance()
                        }
                    }
                }

                val outputIndex = codec.dequeueOutputBuffer(bufferInfo, timeoutUs)
                if (outputIndex >= 0) {
                    if (bufferInfo.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) {
                        outputDone = true
                    }
                    if (bufferInfo.size > 0) {
                        val outBuf = codec.getOutputBuffer(outputIndex)!!
                        val pcm = processOutputBuffer(outBuf, bufferInfo, format)
                        if (pcm != null) {
                            outputBuffers.add(pcm)
                            totalSamples += pcm.size / 2L
                        }
                    }
                    codec.releaseOutputBuffer(outputIndex, false)
                } else if (outputIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) {
                }

                if (totalSamples > maxInputSamples) {
                    outputDone = true
                }
            }

            codec.stop()
            codec.release()
            extractor.release()

            if (outputBuffers.isEmpty()) return null

            val totalSize = outputBuffers.sumOf { it.size }
            val combined = ByteArray(totalSize)
            var offset = 0
            for (buf in outputBuffers) {
                System.arraycopy(buf, 0, combined, offset, buf.size)
                offset += buf.size
            }

            val durationSec = totalSamples / (TARGET_SAMPLE_RATE.toFloat() * TARGET_CHANNELS)

            DecodeResult(
                pcm = combined,
                sampleRate = TARGET_SAMPLE_RATE,
                channels = TARGET_CHANNELS,
                durationSeconds = durationSec
            )
        } catch (e: Exception) {
            android.util.Log.e("AudioDecoder", "Decode failed: ${e.message}", e)
            try { extractor.release() } catch (_: Exception) {}
            null
        }
    }

    private fun selectAudioTrack(extractor: MediaExtractor): Int? {
        for (i in 0 until extractor.trackCount) {
            val format = extractor.getTrackFormat(i)
            val mime = format.getString(MediaFormat.KEY_MIME) ?: continue
            if (mime.startsWith("audio/")) return i
        }
        return null
    }

    private fun processOutputBuffer(
        buf: ByteBuffer,
        info: MediaCodec.BufferInfo,
        format: MediaFormat
    ): ByteArray? {
        if (info.size <= 0) return null
        buf.position(info.offset)
        buf.limit(info.offset + info.size)

        val channelCount = format.getInteger(MediaFormat.KEY_CHANNEL_COUNT, 2)
        val sampleRate = format.getInteger(MediaFormat.KEY_SAMPLE_RATE, TARGET_SAMPLE_RATE)
        val pcmEncoding = format.getInteger(MediaFormat.KEY_PCM_ENCODING, 2)

        val srcBuf: ShortBuffer

        if (pcmEncoding == 4) {
            val bb = ByteArray(info.size)
            buf.get(bb)
            val fb = java.nio.ByteBuffer.wrap(bb).order(ByteOrder.LITTLE_ENDIAN).asFloatBuffer()
            val floatArray = FloatArray(fb.remaining())
            fb.get(floatArray)
            srcBuf = ShortBuffer.wrap(ShortArray(floatArray.size))
            for (i in floatArray.indices) {
                val s = (floatArray[i] * 32767f).toInt().coerceIn(-32768, 32767)
                srcBuf.put(i, s.toShort())
            }
        } else {
            val bb = ByteArray(info.size)
            buf.get(bb)
            val sb = java.nio.ByteBuffer.wrap(bb).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer()
            val shorts = ShortArray(sb.remaining())
            sb.get(shorts)
            srcBuf = ShortBuffer.wrap(shorts)
        }

        // Mix down to mono and resample to 44100
        val result: ShortArray
        if (channelCount == 1 && sampleRate == TARGET_SAMPLE_RATE) {
            result = ShortArray(srcBuf.remaining())
            srcBuf.get(result)
        } else {
            // Mix to mono
            val monoShorts: ShortArray
            if (channelCount > 1) {
                val totalFrames = srcBuf.remaining() / channelCount
                val frameShorts = ShortArray(totalFrames)
                for (f in 0 until totalFrames) {
                    var sum = 0L
                    for (c in 0 until channelCount) {
                        sum += srcBuf.get(f * channelCount + c).toInt()
                    }
                    frameShorts[f] = (sum / channelCount).toInt().coerceIn(-32768, 32767).toShort()
                }
                monoShorts = frameShorts
            } else {
                monoShorts = ShortArray(srcBuf.remaining())
                srcBuf.get(monoShorts)
            }

            // Resample to 44100 if needed
            if (sampleRate != TARGET_SAMPLE_RATE) {
                val ratio = TARGET_SAMPLE_RATE.toDouble() / sampleRate
                val newLen = (monoShorts.size * ratio).toInt()
                val resampled = ShortArray(newLen)
                for (i in 0 until newLen) {
                    val srcIdx = (i / ratio).toInt().coerceAtMost(monoShorts.size - 1)
                    resampled[i] = monoShorts[srcIdx]
                }
                result = resampled
            } else {
                result = monoShorts
            }
        }

        val bb = ByteArray(result.size * 2)
        java.nio.ByteBuffer.wrap(bb).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(result)
        return bb
    }
}
