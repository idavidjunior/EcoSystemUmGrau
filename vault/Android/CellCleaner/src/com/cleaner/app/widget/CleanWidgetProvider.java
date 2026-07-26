package com.cleaner.app.widget;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.widget.RemoteViews;

import com.cleaner.app.R;

public class CleanWidgetProvider extends AppWidgetProvider {

    public static final String ACTION_CLEAN = "com.cleaner.app.CLEAN_NOW";

    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        for (int widgetId : appWidgetIds) {
            Intent intent = new Intent(context, CleanWidgetProvider.class);
            intent.setAction(ACTION_CLEAN);
            PendingIntent pi = PendingIntent.getBroadcast(context, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

            RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.widget_clean);
            views.setOnClickPendingIntent(R.id.widget_root, pi);
            appWidgetManager.updateAppWidget(widgetId, views);
        }
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        super.onReceive(context, intent);
        if (ACTION_CLEAN.equals(intent.getAction())) {
            Intent launchIntent = new Intent();
            launchIntent.setClassName(context, "com.cleaner.app.MainActivity");
            launchIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            launchIntent.putExtra("do_boost", true);
            context.startActivity(launchIntent);
        }
    }
}