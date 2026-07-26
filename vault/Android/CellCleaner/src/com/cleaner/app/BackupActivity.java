package com.cleaner.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Environment;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import android.graphics.drawable.Drawable;

import com.cleaner.app.util.AppManager;
import com.cleaner.app.util.FileUtils;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class BackupActivity extends Activity {

    private ListView appList;
    private Button btnSelectAll, btnBackup;
    private TextView statusText, summaryText;
    private ProgressBar backupProgress;
    private LinearLayout progressSection;

    private List<AppManager.AppInfo> apps;
    private BackupAdapter adapter;
    private boolean[] selected;

    public void closeBackup(View v) { finish(); }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_backup);

        appList = findViewById(R.id.backupAppList);
        btnSelectAll = findViewById(R.id.btnBackupSelectAll);
        btnBackup = findViewById(R.id.btnBackupSelected);
        statusText = findViewById(R.id.backupStatusText);
        summaryText = findViewById(R.id.backupSummaryText);
        backupProgress = findViewById(R.id.backupProgress);
        progressSection = findViewById(R.id.backupProgressSection);

        progressSection.setVisibility(View.GONE);

        loadApps();

        btnSelectAll.setOnClickListener(v -> {
            boolean allSelected = true;
            for (boolean s : selected) { if (!s) { allSelected = false; break; } }
            for (int i = 0; i < selected.length; i++) selected[i] = !allSelected;
            adapter.notifyDataSetChanged();
            updateSummary();
        });

        btnBackup.setOnClickListener(v -> startBackup());
    }

    private void loadApps() {
        new Thread(() -> {
            apps = AppManager.getInstalledApps(BackupActivity.this, true);
            selected = new boolean[apps.size()];
            runOnUiThread(() -> {
                adapter = new BackupAdapter(BackupActivity.this, apps);
                appList.setAdapter(adapter);
                updateSummary();
                statusText.setText(apps.size() + " apps disponíveis para backup.");
            });
        }).start();
    }

    private void updateSummary() {
        int count = 0;
        long total = 0;
        for (int i = 0; i < apps.size(); i++) {
            if (selected[i]) { count++; total += apps.get(i).apkSize; }
        }
        summaryText.setText(count + " selecionados • " + FileUtils.formatSize(total));
    }

    private void startBackup() {
        int count = 0;
        for (boolean s : selected) if (s) count++;
        if (count == 0) { Toast.makeText(this, "Nenhum app selecionado.", Toast.LENGTH_SHORT).show(); return; }

        final int totalToBackup = count;
        progressSection.setVisibility(View.VISIBLE);
        backupProgress.setProgress(0);
        backupProgress.setMax(totalToBackup);
        btnBackup.setEnabled(false);

        File backupDir = new File(Environment.getExternalStorageDirectory(), "CellCleaner/Backups");
        if (!backupDir.exists()) backupDir.mkdirs();

        new Thread(() -> {
            int done = 0;
            int failed = 0;
            long totalSize = 0;

            for (int i = 0; i < apps.size(); i++) {
                if (!selected[i]) continue;
                AppManager.AppInfo app = apps.get(i);
                File apk = AppManager.extractApk(BackupActivity.this, app.packageName, backupDir);
                if (apk != null) {
                    totalSize += apk.length();
                } else {
                    failed++;
                }
                done++;
                final int progress = done;
                runOnUiThread(() -> backupProgress.setProgress(progress));
            }

            final int fFailed = failed;
            final long fTotalSize = totalSize;
            runOnUiThread(() -> {
                btnBackup.setEnabled(true);
                progressSection.setVisibility(View.GONE);
                Toast.makeText(BackupActivity.this,
                    "Backup concluído! " + (totalToBackup - fFailed) + " APKs salvos (" + FileUtils.formatSize(fTotalSize) + ")",
                    Toast.LENGTH_LONG).show();
                statusText.setText("Backup salvo em: " + backupDir.getAbsolutePath());
            });
        }).start();
    }

    private class BackupAdapter extends BaseAdapter {
        private final Context ctx;
        private final List<AppManager.AppInfo> items;

        BackupAdapter(Context ctx, List<AppManager.AppInfo> items) {
            this.ctx = ctx;
            this.items = items;
        }

        @Override public int getCount() { return items.size(); }
        @Override public Object getItem(int i) { return items.get(i); }
        @Override public long getItemId(int i) { return i; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            if (convertView == null) {
                convertView = LayoutInflater.from(ctx).inflate(R.layout.item_app_backup, parent, false);
            }
            AppManager.AppInfo app = items.get(position);

            ImageView icon = convertView.findViewById(R.id.backupAppIcon);
            TextView name = convertView.findViewById(R.id.backupAppName);
            TextView pkg = convertView.findViewById(R.id.backupAppPackage);
            TextView size = convertView.findViewById(R.id.backupAppSize);
            CheckBox check = convertView.findViewById(R.id.backupAppCheck);

            try {
                Drawable d = ctx.getPackageManager().getApplicationIcon(app.packageName);
                icon.setImageDrawable(d);
            } catch (Exception e) {
                icon.setImageResource(android.R.drawable.sym_def_app_icon);
            }
            name.setText(app.appName);
            pkg.setText(app.packageName);
            size.setText(FileUtils.formatSize(app.apkSize));
            check.setChecked(selected[position]);

            check.setOnCheckedChangeListener((b, checked) -> {
                selected[position] = checked;
                updateSummary();
            });

            convertView.setOnClickListener(v -> check.performClick());

            return convertView;
        }
    }
}