package com.cleaner.app.receiver;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

import com.cleaner.app.util.ScheduleManager;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            if (ScheduleManager.isScheduled(context)) {
                int hours = ScheduleManager.getIntervalHours(context);
                ScheduleManager.scheduleClean(context, hours);
            }
        }
    }
}