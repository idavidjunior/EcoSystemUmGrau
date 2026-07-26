package com.cleaner.app.util;

import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.PackageStats;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.Build;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class AppManager {

    public static class AppInfo {
        public String packageName;
        public String appName;
        public Drawable icon;
        public long installedSize;
        public long apkSize;
        public String versionName;
        public long firstInstallTime;
        public long lastUpdateTime;
        public String apkPath;
        public boolean isSystem;

        public String getInstallDateStr() {
            return new SimpleDateFormat("dd/MM/yyyy", Locale.getDefault()).format(new Date(firstInstallTime));
        }
    }

    public static List<AppInfo> getInstalledApps(Context context, boolean includeSystem) {
        List<AppInfo> list = new ArrayList<>();
        try {
            PackageManager pm = context.getPackageManager();
            List<ApplicationInfo> apps = pm.getInstalledApplications(0);
            for (ApplicationInfo ai : apps) {
                try {
                    AppInfo info = new AppInfo();
                    info.packageName = ai.packageName;
                    info.appName = pm.getApplicationLabel(ai).toString();
                    info.icon = pm.getApplicationIcon(ai);
                    info.apkSize = new File(ai.sourceDir).length();
                    info.versionName = pm.getPackageInfo(ai.packageName, 0).versionName;
                    info.firstInstallTime = pm.getPackageInfo(ai.packageName, 0).firstInstallTime;
                    info.lastUpdateTime = pm.getPackageInfo(ai.packageName, 0).lastUpdateTime;
                    info.apkPath = ai.sourceDir;
                    info.isSystem = (ai.flags & ApplicationInfo.FLAG_SYSTEM) != 0;
                    if (!includeSystem && info.isSystem) continue;
                    list.add(info);
                } catch (Exception e) {}
            }
        } catch (Exception e) {}
        Collections.sort(list, (a, b) -> Long.compare(b.apkSize, a.apkSize));
        return list;
    }

    public static void uninstallApp(Context context, String packageName) {
        Intent intent = new Intent(Intent.ACTION_DELETE);
        intent.setData(Uri.parse("package:" + packageName));
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(intent);
    }

    public static File extractApk(Context context, String packageName, File outputDir) {
        try {
            PackageManager pm = context.getPackageManager();
            ApplicationInfo ai = pm.getApplicationInfo(packageName, 0);
            File src = new File(ai.sourceDir);
            if (!src.exists()) return null;
            if (!outputDir.exists()) outputDir.mkdirs();
            String appName = pm.getApplicationLabel(ai).toString().replaceAll("[\\\\/:*?\"<>|]", "_");
            File dest = new File(outputDir, appName + "_" + ai.packageName + ".apk");
            FileInputStream fis = new FileInputStream(src);
            FileOutputStream fos = new FileOutputStream(dest);
            byte[] buf = new byte[8192];
            int len;
            while ((len = fis.read(buf)) > 0) fos.write(buf, 0, len);
            fis.close();
            fos.close();
            return dest;
        } catch (Exception e) { return null; }
    }
}