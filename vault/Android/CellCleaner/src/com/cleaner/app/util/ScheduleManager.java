package com.cleaner.app.util;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;

import com.cleaner.app.receiver.CleanAlarmReceiver;

public class ScheduleManager {

    private static final String PREFS_SCHEDULE = "schedule_prefs";
    private static final String KEY_INTERVAL = "schedule_interval";
    private static final String KEY_ENABLED = "schedule_enabled";

    public static void scheduleClean(Context context, int intervalHours) {
        AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        Intent intent = new Intent(context, CleanAlarmReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        long intervalMs = intervalHours * 3600L * 1000L;
        long triggerAt = System.currentTimeMillis() + intervalMs;

        if (Build.VERSION.SDK_INT >= 23) {
            am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pi);
        } else {
            am.set(AlarmManager.RTC_WAKEUP, triggerAt, pi);
        }

        context.getSharedPreferences(PREFS_SCHEDULE, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(KEY_ENABLED, true)
            .putInt(KEY_INTERVAL, intervalHours)
            .apply();
    }

    public static void cancelSchedule(Context context) {
        AlarmManager am = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        Intent intent = new Intent(context, CleanAlarmReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        am.cancel(pi);

        context.getSharedPreferences(PREFS_SCHEDULE, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(KEY_ENABLED, false)
            .apply();
    }

    public static boolean isScheduled(Context context) {
        return context.getSharedPreferences(PREFS_SCHEDULE, Context.MODE_PRIVATE)
            .getBoolean(KEY_ENABLED, false);
    }

    public static int getIntervalHours(Context context) {
        return context.getSharedPreferences(PREFS_SCHEDULE, Context.MODE_PRIVATE)
            .getInt(KEY_INTERVAL, 24);
    }
}