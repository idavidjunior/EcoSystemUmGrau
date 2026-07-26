package com.cleaner.app.util;

import android.content.Context;
import android.content.res.Configuration;
import android.os.Build;
import android.util.DisplayMetrics;
import android.view.WindowManager;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.Locale;

public class DeviceInfo {

    public static class DeviceData {
        public String manufacturer;
        public String model;
        public String androidVersion;
        public int sdkInt;
        public String cpu;
        public int cores;
        public String resolution;
        public float density;
        public long totalStorage;
        public String language;
        public int displayWidth;
        public int displayHeight;
    }

    public static DeviceData getDeviceData(Context context) {
        DeviceData d = new DeviceData();
        d.manufacturer = Build.MANUFACTURER;
        d.model = Build.MODEL;
        d.androidVersion = Build.VERSION.RELEASE;
        d.sdkInt = Build.VERSION.SDK_INT;
        d.cpu = getCpuName();
        d.cores = Runtime.getRuntime().availableProcessors();
        d.language = Locale.getDefault().getDisplayLanguage();

        try {
            WindowManager wm = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
            DisplayMetrics dm = new DisplayMetrics();
            wm.getDefaultDisplay().getRealMetrics(dm);
            d.displayWidth = dm.widthPixels;
            d.displayHeight = dm.heightPixels;
            d.density = dm.density;
            d.resolution = dm.widthPixels + "x" + dm.heightPixels;
        } catch (Exception e) {}

        d.totalStorage = android.os.Environment.getExternalStorageDirectory().getTotalSpace();
        return d;
    }

    private static String getCpuName() {
        try {
            BufferedReader br = new BufferedReader(new FileReader("/proc/cpuinfo"));
            String line;
            while ((line = br.readLine()) != null) {
                if (line.contains("Hardware") || line.contains("Processor") || line.contains("model name")) {
                    br.close();
                    return line.split(":")[1].trim();
                }
            }
            br.close();
        } catch (Exception e) {}
        return Build.CPU_ABI != null ? Build.CPU_ABI : "Desconhecido";
    }
}