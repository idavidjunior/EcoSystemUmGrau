package com.cleaner.app.util;

import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Build;

public class BatteryInfo {

    public static class BatteryData {
        public int level;
        public int scale;
        public int temperature; // in tenths of Celsius
        public int voltage;     // in mV
        public int status;      // BatteryManager.BATTERY_STATUS_*
        public int health;      // BatteryManager.BATTERY_HEALTH_*
        public int plugged;
        public String technology;

        public int getPercent() { return scale > 0 ? level * 100 / scale : level; }
        public float getTempCelsius() { return temperature / 10f; }
        public boolean isCharging() {
            return status == BatteryManager.BATTERY_STATUS_CHARGING
                || status == BatteryManager.BATTERY_STATUS_FULL;
        }
        public String getStatusStr() {
            switch (status) {
                case BatteryManager.BATTERY_STATUS_CHARGING: return "Carregando";
                case BatteryManager.BATTERY_STATUS_DISCHARGING: return "Descarregando";
                case BatteryManager.BATTERY_STATUS_FULL: return "Cheia";
                case BatteryManager.BATTERY_STATUS_NOT_CHARGING: return "Não carregando";
                default: return "Desconhecido";
            }
        }
        public String getHealthStr() {
            switch (health) {
                case BatteryManager.BATTERY_HEALTH_GOOD: return "Boa";
                case BatteryManager.BATTERY_HEALTH_OVERHEAT: return "Superaquecida";
                case BatteryManager.BATTERY_HEALTH_DEAD: return "Morta";
                case BatteryManager.BATTERY_HEALTH_OVER_VOLTAGE: return "Sobretensão";
                case BatteryManager.BATTERY_HEALTH_COLD: return "Fria";
                default: return "Desconhecida";
            }
        }
    }

    public static BatteryData getBatteryData(Context context) {
        BatteryData data = new BatteryData();
        try {
            Intent intent = context.registerReceiver(null,
                new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
            if (intent != null) {
                data.level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, 0);
                data.scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, 100);
                data.temperature = intent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0);
                data.voltage = intent.getIntExtra(BatteryManager.EXTRA_VOLTAGE, 0);
                data.status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
                data.health = intent.getIntExtra(BatteryManager.EXTRA_HEALTH, -1);
                data.plugged = intent.getIntExtra(BatteryManager.EXTRA_PLUGGED, -1);
                data.technology = intent.getStringExtra(BatteryManager.EXTRA_TECHNOLOGY);
            }
        } catch (Exception e) {}
        return data;
    }
}