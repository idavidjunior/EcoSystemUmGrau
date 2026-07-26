package com.cleaner.app.receiver;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

import com.cleaner.app.MainActivity;
import com.cleaner.app.R;

public class CleanAlarmReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        String channelId = "cellcleaner_schedule";
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel ch = new NotificationChannel(channelId, "Limpeza Agendada",
                NotificationManager.IMPORTANCE_DEFAULT);
            ((NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE)).createNotificationChannel(ch);
        }

        Intent i = new Intent(context, MainActivity.class);
        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(context, 0, i,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        NotificationManager nm = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        android.app.Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= 26) {
            builder = new android.app.Notification.Builder(context, channelId);
        } else {
            builder = new android.app.Notification.Builder(context);
        }
        builder.setContentTitle("Hora de limpar!")
               .setContentText("Toque para abrir o Cell Cleaner e escanear seu dispositivo.")
               .setSmallIcon(android.R.drawable.ic_menu_manage)
               .setContentIntent(pi)
               .setAutoCancel(true);

        if (Build.VERSION.SDK_INT >= 26) {
            nm.notify(1001, builder.build());
        } else {
            nm.notify(1001, builder.getNotification());
        }
    }
}