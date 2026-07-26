package com.cleaner.app;

import android.os.Environment;
import android.os.StatFs;
import android.util.Log;
import com.cleaner.app.model.JunkCategory;
import com.cleaner.app.model.JunkItem;
import com.cleaner.app.util.FileUtils;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class ScanEngine extends Thread {

    public interface ScanListener {
        void onProgress(int percent, String status);
        void onComplete(List<JunkCategory> categories, long totalSize);
        void onError(String message);
    }

    private final ScanListener listener;
    private final boolean deepScan;
    private final boolean includeMedia;
    private final List<String> extraRoots;
    private volatile boolean cancelled;
    private List<JunkCategory> categories;
    private long totalJunkSize;

    private static final long LARGE_FILE_THRESHOLD = 20L * 1024 * 1024; // 20MB
    private static final String TAG = "ScanEngine";

    public ScanEngine(ScanListener listener, boolean deepScan, boolean includeMedia) {
        this(listener, deepScan, includeMedia, null);
    }

    public ScanEngine(ScanListener listener, boolean deepScan, boolean includeMedia, List<String> extraRoots) {
        this.listener = listener;
        this.deepScan = deepScan;
        this.includeMedia = includeMedia;
        this.extraRoots = extraRoots;
        this.cancelled = false;
    }

    public void cancel() {
        cancelled = true;
    }

    @Override
    public void run() {
        try {
            scan();
        } catch (Exception e) {
            Log.e(TAG, "Scan error", e);
            if (listener != null && !cancelled) {
                listener.onError("Erro ao escanear: " + e.getMessage());
            }
        }
    }

    private void scan() {
        categories = new ArrayList<>();
        JunkCategory cacheCat = new JunkCategory(JunkItem.TYPE_CACHE, "Arquivos de Cache", "cache");
        JunkCategory tempCat = new JunkCategory(JunkItem.TYPE_TEMP, "Arquivos Temporários", "temp");
        JunkCategory apkCat = new JunkCategory(JunkItem.TYPE_APK, "APKs Instalados", "apk");
        JunkCategory logCat = new JunkCategory(JunkItem.TYPE_LOG, "Arquivos de Log", "log");
        JunkCategory emptyCat = new JunkCategory(JunkItem.TYPE_EMPTY_DIR, "Pastas Vazias", "folder");
        JunkCategory largeCat = new JunkCategory(JunkItem.TYPE_LARGE_FILE, "Arquivos Grandes", "large");

        categories.add(cacheCat);
        categories.add(tempCat);
        categories.add(apkCat);
        categories.add(logCat);
        categories.add(emptyCat);
        categories.add(largeCat);

        publishProgress(5, "Preparando scan…");

        File extStorage = Environment.getExternalStorageDirectory();
        if (extStorage == null || !extStorage.exists()) {
            publishProgress(100, "Armazenamento não disponível");
            return;
        }

        // Phase 1: Walk storage tree (5-90%)
        int maxDepth = deepScan ? 6 : 4;
        if (!cancelled) {
            scanDirectory(extStorage, cacheCat, tempCat, apkCat, logCat, emptyCat, largeCat, maxDepth, 0);

            // Also scan extra roots (SD cards, etc.)
            if (extraRoots != null) {
                for (String extraPath : extraRoots) {
                    if (cancelled) break;
                    File extraDir = new File(extraPath);
                    if (extraDir.exists() && extraDir.isDirectory()
                        && !extraDir.getAbsolutePath().equals(extStorage.getAbsolutePath())) {
                        scanDirectory(extraDir, cacheCat, tempCat, apkCat, logCat, emptyCat, largeCat, maxDepth, 0);
                    }
                }
            }
        }

        // Phase 2: Post-process (90-95%)
        publishProgress(92, "Processando resultados…");

        List<JunkCategory> toRemove = new ArrayList<>();
        for (JunkCategory cat : categories) {
            if (cat.getItemCount() == 0) toRemove.add(cat);
        }
        categories.removeAll(toRemove);

        totalJunkSize = 0;
        for (JunkCategory cat : categories) {
            totalJunkSize += cat.getTotalSize();
        }

        publishProgress(100, "Escaneamento concluído!");

        if (listener != null && !cancelled) {
            listener.onComplete(categories, totalJunkSize);
        }
    }

    private void scanDirectory(File dir,
                               JunkCategory cacheCat, JunkCategory tempCat,
                               JunkCategory apkCat, JunkCategory logCat,
                               JunkCategory emptyCat, JunkCategory largeCat) {
        scanDirectory(dir, cacheCat, tempCat, apkCat, logCat, emptyCat, largeCat, -1, 0);
    }

    private void scanDirectory(File dir,
                               JunkCategory cacheCat, JunkCategory tempCat,
                               JunkCategory apkCat, JunkCategory logCat,
                               JunkCategory emptyCat, JunkCategory largeCat,
                               int maxDepth, int currentDepth) {
        if (cancelled || dir == null || !dir.exists()) return;
        if (maxDepth >= 0 && currentDepth > maxDepth) return;

        // Skip protected directories
        String absPath = dir.getAbsolutePath().toLowerCase();
        if (absPath.contains("/android/data") || absPath.contains("/android/obb")) return;

        File[] children = dir.listFiles();
        if (children == null) return;

        for (File child : children) {
            if (cancelled) return;

            try {
                String name = child.getName().toLowerCase();

                if (child.isDirectory()) {
                    if (name.contains("cache") || name.contains("trash") || name.contains("lixo")) {
                        cacheCat.items.add(new JunkItem(child, JunkItem.TYPE_CACHE));
                    } else if (name.equals("temp") || name.equals("tmp") || name.contains("temp")) {
                        tempCat.items.add(new JunkItem(child, JunkItem.TYPE_TEMP));
                    } else if (name.equals(".thumbnails")) {
                        cacheCat.items.add(new JunkItem(child, JunkItem.TYPE_CACHE));
                    } else {
                        // Check if empty before recursing
                        File[] subFiles = child.listFiles();
                        if (subFiles != null && subFiles.length == 0) {
                            emptyCat.items.add(new JunkItem(child, JunkItem.TYPE_EMPTY_DIR));
                        } else if (subFiles != null) {
                            // Recurse into non-empty subdirectory
                            scanDirectory(child, cacheCat, tempCat, apkCat, logCat, emptyCat, largeCat,
                                         maxDepth, currentDepth + 1);
                        }
                    }
                } else if (child.isFile()) {
                    long fileSize = child.length();

                    if (FileUtils.isApkFile(child)) {
                        apkCat.items.add(new JunkItem(child, JunkItem.TYPE_APK));
                    } else if (FileUtils.isLogFile(child)) {
                        logCat.items.add(new JunkItem(child, JunkItem.TYPE_LOG));
                    } else if (FileUtils.isTempFile(child)) {
                        tempCat.items.add(new JunkItem(child, JunkItem.TYPE_TEMP));
                    } else if (fileSize >= LARGE_FILE_THRESHOLD) {
                        boolean isMedia = isMediaFile(child);
                        if (includeMedia || !isMedia) {
                            if (!name.equals(""))
                                largeCat.items.add(new JunkItem(child, JunkItem.TYPE_LARGE_FILE));
                        }
                    }
                }
            } catch (Exception e) {
                // Skip files that can't be accessed
            }
        }
    }

    private boolean isMediaFile(File file) {
        String name = file.getName().toLowerCase();
        return name.endsWith(".mp4") || name.endsWith(".mkv") || name.endsWith(".avi") ||
               name.endsWith(".mp3") || name.endsWith(".wav") || name.endsWith(".flac") ||
               name.endsWith(".jpg") || name.endsWith(".jpeg") || name.endsWith(".png") ||
               name.endsWith(".gif") || name.endsWith(".zip") || name.endsWith(".rar");
    }

    private void publishProgress(int percent, String status) {
        if (listener != null && !cancelled) {
            listener.onProgress(Math.min(percent, 100), status);
        }
    }

    public static String getStorageInfo() {
        try {
            StatFs stat = new StatFs(Environment.getExternalStorageDirectory().getAbsolutePath());
            long totalBytes = stat.getTotalBytes();
            long freeBytes = stat.getAvailableBytes();
            long usedBytes = totalBytes - freeBytes;
            return FileUtils.formatSize(usedBytes) + " usado / " +
                   FileUtils.formatSize(freeBytes) + " livre de " +
                   FileUtils.formatSize(totalBytes);
        } catch (Exception e) {
            return "Indisponível";
        }
    }

    public static long getTotalStorage() {
        try {
            StatFs stat = new StatFs(Environment.getExternalStorageDirectory().getAbsolutePath());
            return stat.getTotalBytes();
        } catch (Exception e) {
            return 0;
        }
    }

    public static long getFreeStorage() {
        try {
            StatFs stat = new StatFs(Environment.getExternalStorageDirectory().getAbsolutePath());
            return stat.getAvailableBytes();
        } catch (Exception e) {
            return 0;
        }
    }

    public static long getUsedStorage() {
        return getTotalStorage() - getFreeStorage();
    }
}
