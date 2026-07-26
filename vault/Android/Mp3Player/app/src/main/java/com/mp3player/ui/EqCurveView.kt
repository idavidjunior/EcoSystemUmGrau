package com.mp3player.ui

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.util.AttributeSet
import android.view.View

class EqCurveView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    var levels: FloatArray = FloatArray(0)
        set(value) { field = value; invalidate() }
    var minLevel: Int = -12
    var maxLevel: Int = 12

    private val barPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(80, 0, 191, 255)
        style = Paint.Style.FILL
    }
    private val barActivePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(180, 0, 191, 255)
        style = Paint.Style.FILL
    }
    private val gridPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(25, 255, 255, 255)
        strokeWidth = 1f
    }
    private val centerLinePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(50, 255, 255, 255)
        strokeWidth = 1f
    }
    private val linePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(220, 0, 191, 255)
        strokeWidth = 3f
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }
    private val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(40, 0, 191, 255)
        style = Paint.Style.FILL
    }
    private val dotPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(240, 0, 191, 255)
        style = Paint.Style.FILL
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val h = height.toFloat()
        if (w <= 0 || h <= 0 || levels.isEmpty()) return

        val centerY = h * 0.6f
        val range = (maxLevel - minLevel).coerceAtLeast(1)
        val barCount = levels.size
        val barGap = 4f
        val barWidth = ((w - barGap * (barCount + 1)) / barCount).coerceAtMost(32f)

        // Horizontal grid lines
        for (gl in intArrayOf(-12, -6, 0, 6, 12)) {
            val frac = (gl - minLevel).toFloat() / range
            val y = centerY - (frac - 0.5f) * h * 0.75f
            if (y in 0f..h) {
                canvas.drawLine(0f, y, w, y, gridPaint)
            }
        }
        canvas.drawLine(0f, centerY, w, centerY, centerLinePaint)

        // Spectrum bars + curve points
        val points = mutableListOf<Pair<Float, Float>>()
        val baseline = (h * 0.88f)

        for (i in levels.indices) {
            val frac = (levels[i] - minLevel) / range
            val barHeight = (frac - 0.5f) * h * 0.75f
            val x = barGap + i * (barWidth + barGap)
            val topY = centerY - barHeight
            val bottomY = centerY.coerceAtMost(baseline)

            // Draw bar
            val paint = if (levels[i] > 0) barActivePaint else barPaint
            if (barHeight > 0) {
                canvas.drawRect(x, topY, x + barWidth, bottomY, paint)
            } else {
                canvas.drawRect(x, bottomY, x + barWidth, bottomY - barHeight, paint)
            }

            // Curve point at top of bar
            points.add((x + barWidth / 2f) to topY.coerceIn(0f, h))
        }

        // Bezier curve overlay on bars
        if (points.size >= 2) {
            val path = Path()
            path.moveTo(points[0].first, points[0].second)
            for (i in 1 until points.size) {
                val cx = (points[i - 1].first + points[i].first) / 2f
                path.cubicTo(cx, points[i - 1].second, cx, points[i].second, points[i].first, points[i].second)
            }

            val fillPath = Path(path)
            fillPath.lineTo(points.last().first, baseline)
            fillPath.lineTo(points.first().first, baseline)
            fillPath.close()
            canvas.drawPath(fillPath, fillPaint)
            canvas.drawPath(path, linePaint)

            for ((x, y) in points) {
                canvas.drawCircle(x, y, 4f, dotPaint)
            }
        }
    }
}
