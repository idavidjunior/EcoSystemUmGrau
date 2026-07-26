package com.cleaner.app.util;

import android.content.Context;
import android.os.Build;
import android.os.Environment;
import android.os.StatFs;
import android.os.storage.StorageManager;
import android.os.storage.StorageVolume;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class StorageUtil {

    public static class VolumeInfo {
        public String path;
        public String label;
        public long totalBytes;
        public long freeBytes;
        public boolean isPrimary;

        public long getUsedBytes() { return totalBytes - freeBytes; }
        public int getUsedPercent() {
            if (totalBytes <= 0) return 0;
            return (int)(getUsedBytes() * 100 / totalBytes);
        }
    }

    public static List<VolumeInfo> getAllVolumes(Context context) {
        List<VolumeInfo> volumes = new ArrayList<>();

        // Primary internal storage
        VolumeInfo primary = new VolumeInfo();
        primary.path = Environment.getExternalStorageDirectory().getAbsolutePath();
        primary.label = "Armazenamento Interno";
        primary.isPrimary = true;
        getVolumeStats(primary);
        volumes.add(primary);

        // Secondary volumes (SD cards)
        if (Build.VERSION.SDK_INT >= 24) {
            try {
                StorageManager sm = (StorageManager) context.getSystemService(Context.STORAGE_SERVICE);
                List<StorageVolume> storageVolumes = sm.getStorageVolumes();
                for (StorageVolume sv : storageVolumes) {
                    try {
                        File dir = sv.getDirectory();
                        if (dir == null) continue;
                        String path = dir.getAbsolutePath();
                        if (path.equals(primary.path)) continue;

                        VolumeInfo vol = new VolumeInfo();
                        vol.path = path;
                        vol.label = sv.getDescription(context);
                        vol.isPrimary = false;
                        getVolumeStats(vol);
                        if (vol.totalBytes > 0) {
                            volumes.add(vol);
                        }
                    } catch (Exception e) {
                        // Skip inaccessible volumes
                    }
                }
            } catch (Exception e) {
                // StorageManager not available
            }
        } else {
            // Try /storage/extSdCard or common SD card paths
            String[] sdPaths = {"/storage/extSdCard", "/storage/sdcard1", "/storage/external_SD",
                                "/mnt/sdcard1", "/mnt/extSdCard"};
            for (String path : sdPaths) {
                File f = new File(path);
                if (f.exists() && f.isDirectory() && !f.getAbsolutePath().equals(primary.path)) {
                    VolumeInfo vol = new VolumeInfo();
                    vol.path = path;
                    vol.label = "Cartão SD";
                    vol.isPrimary = false;
                    getVolumeStats(vol);
                    if (vol.totalBytes > 0) {
                        volumes.add(vol);
                    }
                }
            }
        }

        return volumes;
    }

    private static void getVolumeStats(VolumeInfo vol) {
        try {
            StatFs stat = new StatFs(vol.path);
            vol.totalBytes = stat.getTotalBytes();
            vol.freeBytes = stat.getAvailableBytes();
        } catch (Exception e) {
            vol.totalBytes = 0;
            vol.freeBytes = 0;
        }
    }

    public static boolean hasSdCard(Context context) {
        List<VolumeInfo> vols = getAllVolumes(context);
        for (VolumeInfo v : vols) {
            if (!v.isPrimary) return true;
        }
        return false;
    }
}