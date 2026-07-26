package com.cleaner.app.util;

import java.io.File;
import java.text.DecimalFormat;

public class FileUtils {
    private static final String[] SIZE_UNITS = {"B", "KB", "MB", "GB"};
    private static final DecimalFormat DF = new DecimalFormat("#.#");

    public static String formatSize(long bytes) {
        if (bytes <= 0) return "0 B";
        int unitIndex = 0;
        double size = bytes;
        while (size >= 1024 && unitIndex < SIZE_UNITS.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        if (unitIndex == 0) return (long) size + " " + SIZE_UNITS[unitIndex];
        return DF.format(size) + " " + SIZE_UNITS[unitIndex];
    }

    public static boolean deleteFile(File file) {
        if (file == null || !file.exists()) return true;
        if (file.isDirectory()) {
            File[] children = file.listFiles();
            if (children != null) {
                for (File child : children) {
                    deleteFile(child);
                }
            }
        }
        return file.delete();
    }

    public static boolean canRead(File file) {
        return file != null && file.exists() && file.canRead();
    }

    public static boolean isCacheDir(File dir) {
        return dir != null && dir.isDirectory() &&
               dir.getName().toLowerCase().equals("cache");
    }

    public static boolean isTempFile(File file) {
        if (file == null || !file.isFile()) return false;
        String name = file.getName().toLowerCase();
        return name.endsWith(".tmp") || name.endsWith(".temp") || name.endsWith("_tmp") ||
               name.endsWith(".bak") || name.endsWith(".thumbdata") ||
               name.contains("thumbcache") || name.endsWith(".cache");
    }

    public static boolean isApkFile(File file) {
        return file != null && file.isFile() &&
               file.getName().toLowerCase().endsWith(".apk");
    }

    public static boolean isLogFile(File file) {
        if (file == null || !file.isFile()) return false;
        String name = file.getName().toLowerCase();
        return name.endsWith(".log") || name.endsWith(".logs") ||
               name.endsWith(".trace") || name.endsWith(".dump");
    }

    public static boolean isEmptyDir(File dir) {
        if (dir == null || !dir.isDirectory()) return false;
        File[] children = dir.listFiles();
        return children == null || children.length == 0;
    }

    public static boolean isLargeFile(File file, long thresholdBytes) {
        return file != null && file.isFile() && file.length() >= thresholdBytes;
    }

    public static long getDirectorySize(File dir) {
        long size = 0;
        if (dir == null || !dir.exists()) return 0;
        if (dir.isFile()) return dir.length();
        File[] children = dir.listFiles();
        if (children == null) return 0;
        for (File child : children) {
            size += getDirectorySize(child);
        }
        return size;
    }
}
