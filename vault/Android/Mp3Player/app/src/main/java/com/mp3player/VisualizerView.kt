package com.mp3player

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import kotlin.random.Random

class VisualizerView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val bars = mutableListOf<VisualBar>()
    private val barCount = 7
    private var animator: ValueAnimator? = null
    var isAnimating: Boolean = false
        private set

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#1DB954")
        style = Paint.Style.FILL
    }

    private val inactivePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.parseColor("#333333")
        style = Paint.Style.FILL
    }

    init {
        for (i in 0 until barCount) {
            bars.add(VisualBar(height = Random.nextFloat() * 0.8f + 0.2f))
        }
    }

    fun startAnimating() {
        if (isAnimating) return
        isAnimating = true
        animator = ValueAnimator.ofFloat(0f, 1f).apply {
            duration = 300
            repeatCount = ValueAnimator.INFINITE
            repeatMode = ValueAnimator.REVERSE
            addUpdateListener {
                bars.forEach { bar ->
                    bar.height = (0.15f + Random.nextFloat() * 0.85f)
                }
                invalidate()
            }
            start()
        }
    }

    fun stopAnimating() {
        isAnimating = false
        animator?.cancel()
        animator = null
        bars.forEach { it.height = 0.15f }
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val gap = 4f
        val totalGaps = gap * (barCount - 1)
        val barWidth = (width - totalGaps) / barCount
        val maxHeight = height * 0.85f

        bars.forEachIndexed { i, bar ->
            val barHeight = maxHeight * bar.height
            val left = i * (barWidth + gap)
            val top = height - barHeight
            rect.set(left, top, left + barWidth, height.toFloat() - 2f)
            canvas.drawRoundRect(rect, 3f, 3f, if (isAnimating) paint else inactivePaint)
        }
    }

    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()
        stopAnimating()
    }

    private val rect = RectF()

    data class VisualBar(var height: Float)
}
