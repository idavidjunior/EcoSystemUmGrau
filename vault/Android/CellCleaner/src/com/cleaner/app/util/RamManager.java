package com.cleaner.app.util;

import android.app.ActivityManager;
import android.content.Context;
import android.os.Debug;

import java.io.File;
import java.util.List;

public class RamManager {

    public static class RamInfo {
        public long totalRam;
        public long usedRam;
        public long freeRam;
        public long availableRam;
        public boolean isLow;

        public int getUsedPercent() {
            if (totalRam <= 0) return 0;
            return (int)(usedRam * 100 / totalRam);
        }
    }

    public static RamInfo getRamInfo(Context context) {
        RamInfo info = new RamInfo();
        try {
            ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
            am.getMemoryInfo(mi);
            info.totalRam = mi.totalMem;
            info.availableRam = mi.availMem;
            info.usedRam = info.totalRam - info.availableRam;
            info.isLow = mi.lowMemory;
        } catch (Exception e) {
            info.totalRam = Runtime.getRuntime().totalMemory();
            info.usedRam = info.totalRam - Runtime.getRuntime().freeMemory();
            info.availableRam = Runtime.getRuntime().freeMemory();
        }
        return info;
    }

    public static long cleanRam(Context context) {
        long before = getRamInfo(context).availableRam;
        try {
            for (int i = 0; i < 5; i++) {
                System.gc();
                Runtime.getRuntime().gc();
                try { Thread.sleep(50); } catch (Exception e) {}
            }

            ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            List<ActivityManager.RunningAppProcessInfo> procs = am.getRunningAppProcesses();
            if (procs != null) {
                for (ActivityManager.RunningAppProcessInfo proc : procs) {
                    if (proc.importance > ActivityManager.RunningAppProcessInfo.IMPORTANCE_VISIBLE
                        && proc.importance <= ActivityManager.RunningAppProcessInfo.IMPORTANCE_CACHED) {
                        try { am.killBackgroundProcesses(proc.processName); } catch (Exception e) {}
                    }
                }
            }

            for (int i = 0; i < 3; i++) {
                System.gc();
                try { Thread.sleep(50); } catch (Exception e) {}
            }
        } catch (Exception e) {}

        long after = getRamInfo(context).availableRam;
        return Math.max(after - before, 0);
    }

    public static long getAppCacheSize(Context context) {
        long total = 0;
        try {
            // External cache dirs
            File extCache = context.getExternalCacheDir();
            if (extCache != null) total += getDirSize(extCache);
            // Internal cache
            total += getDirSize(context.getCacheDir());
            // Code cache
            File codeCache = context.getCodeCacheDir();
            if (codeCache != null) total += getDirSize(codeCache);
        } catch (Exception e) {}
        return total;
    }

    public static long cleanAppCache(Context context) {
        long before = getAppCacheSize(context);
        try {
            File extCache = context.getExternalCacheDir();
            if (extCache != null) deleteDirContents(extCache);
            deleteDirContents(context.getCacheDir());
            File codeCache = context.getCodeCacheDir();
            if (codeCache != null) deleteDirContents(codeCache);
        } catch (Exception e) {}
        long after = getAppCacheSize(context);
        return before - after;
    }

    public static int getRunningProcessCount(Context context) {
        try {
            ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            List<ActivityManager.RunningAppProcessInfo> procs = am.getRunningAppProcesses();
            return procs != null ? procs.size() : 0;
        } catch (Exception e) { return 0; }
    }

    private static long getDirSize(File dir) {
        if (dir == null || !dir.exists()) return 0;
        long size = 0;
        File[] files = dir.listFiles();
        if (files == null) return 0;
        for (File f : files) {
            size += f.isDirectory() ? getDirSize(f) : f.length();
        }
        return size;
    }

    private static void deleteDirContents(File dir) {
        if (dir == null || !dir.exists()) return;
        File[] files = dir.listFiles();
        if (files == null) return;
        for (File f : files) {
            FileUtils.deleteFile(f);
        }
    }
}