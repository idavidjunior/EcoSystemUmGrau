package com.mp3player

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews

class PlayerWidget : AppWidgetProvider() {

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (appWidgetId in appWidgetIds) {
            updateAppWidget(context, appWidgetManager, appWidgetId)
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (PlayerService.ACTION_PLAY_STATE_CHANGED == intent.action) {
            val isPlaying = intent.getBooleanExtra("is_playing", false)
            val appWidgetManager = AppWidgetManager.getInstance(context)
            val appWidgetIds = appWidgetManager.getAppWidgetIds(
                android.content.ComponentName(context, PlayerWidget::class.java)
            )
            for (appWidgetId in appWidgetIds) {
                val views = RemoteViews(context.packageName, R.layout.player_widget)
                views.setImageViewResource(R.id.widget_play,
                    if (isPlaying) R.drawable.ic_pause
                    else R.drawable.ic_play_arrow)
                setupPendingIntents(context, views)
                appWidgetManager.updateAppWidget(appWidgetId, views)
            }
        }
    }

    private fun updateAppWidget(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int) {
        val views = RemoteViews(context.packageName, R.layout.player_widget)
        setupPendingIntents(context, views)
        appWidgetManager.updateAppWidget(appWidgetId, views)
    }

    private fun setupPendingIntents(context: Context, views: RemoteViews) {
        val toggleIntent = Intent(context, PlayerService::class.java).apply { action = PlayerService.ACTION_TOGGLE }
        val nextIntent = Intent(context, PlayerService::class.java).apply { action = PlayerService.ACTION_NEXT }
        val prevIntent = Intent(context, PlayerService::class.java).apply { action = PlayerService.ACTION_PREV }

        views.setOnClickPendingIntent(R.id.widget_play,
            PendingIntent.getService(context, 0, toggleIntent, PendingIntent.FLAG_IMMUTABLE))
        views.setOnClickPendingIntent(R.id.widget_next,
            PendingIntent.getService(context, 1, nextIntent, PendingIntent.FLAG_IMMUTABLE))
        views.setOnClickPendingIntent(R.id.widget_prev,
            PendingIntent.getService(context, 2, prevIntent, PendingIntent.FLAG_IMMUTABLE))
    }
}
