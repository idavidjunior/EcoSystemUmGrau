package com.cleaner.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.View;
import android.widget.*;
import android.util.Log;

import com.cleaner.app.adapter.JunkAdapter;
import com.cleaner.app.model.JunkCategory;
import com.cleaner.app.model.JunkItem;
import com.cleaner.app.util.AppManager;
import com.cleaner.app.util.BatteryInfo;
import com.cleaner.app.util.DeviceInfo;
import com.cleaner.app.util.DuplicateScanner;
import com.cleaner.app.util.FileUtils;
import com.cleaner.app.util.RamManager;
import com.cleaner.app.util.ReportExporter;
import com.cleaner.app.util.ScheduleManager;
import com.cleaner.app.util.StorageUtil;
import com.cleaner.app.util.WhatsAppCleaner;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends Activity {

    private static final String PREFS_NAME = "cellcleaner_prefs";
    private static final String KEY_THEME = "theme";
    private static final String KEY_DEEP_SCAN = "deep_scan";
    private static final String KEY_INCLUDE_MEDIA = "include_media";
    private static final int THEME_LIGHT = 0;
    private static final int THEME_DARK = 1;
    private static final int THEME_SYSTEM = 2;
    private static final int REQUEST_MANAGE_STORAGE = 1001;

    private SharedPreferences prefs;
    private int currentTheme = THEME_LIGHT;

    // Views
    private View pageScan, pageResults, pageSettings, pageStorage;
    private View tabScan, tabResults, tabSettings, tabStorage;
    private ImageView tabScanIcon, tabResultsIcon, tabSettingsIcon, tabStorageIcon;
    private TextView tabScanLabel, tabResultsLabel, tabSettingsLabel, tabStorageLabel;

    // Scan page
    private ImageView scanButton;
    private TextView scanTitle, scanSubtitle, scanStatus;
    private ProgressBar scanProgress;
    private TextView statsTotalValue, statsItemsValue, statsCleanedValue;
    private TextView storageUsedLabel, storageFreeLabel, storageTotalLabel;
    private TextView tipText;

    // Results page
    private ListView resultsList;
    private TextView resultsSummarySize;
    private Button btnSelectAll, btnCleanSelected;
    private LinearLayout bottomActionBar, resultsHeader;

    // Settings page
    private TextView themeLight, themeDark, themeSystem;
    private CheckBox chkDeepScan, chkIncludeMedia;
    private Button btnManagePermissions;

    // Storage page
    private ProgressBar storageBarInternal, storageBarSd, ramBar;
    private TextView storageUsedLabelInternal, storageFreeLabelInternal, storageTotalLabelInternal;
    private TextView storageUsedLabelSd, storageFreeLabelSd, storageTotalLabelSd;
    private View sdCardSection;
    private TextView spaceApps, spaceMedia, spaceCache, spaceOther;
    private TextView ramUsedLabel, ramFreeLabel, ramTotalLabel, ramProcessCount, appCacheSize;
    private Button btnCleanRam, btnCleanAppCache;
    private TextView deviceModel, deviceAndroid, deviceCpu, deviceScreen;
    private ProgressBar batteryBar;
    private TextView batteryLevel, batteryStatus, batteryTemp, batteryHealth;
    private Button btnBoost, btnOpenAppManager, btnScanDup, btnScanWhatsapp, btnExportReport;
    private TextView dupStatus, whatsappStatus;
    private CheckBox chkSchedule;
    private EditText scheduleInterval;

    // Data
    private List<JunkCategory> categories;
    private JunkAdapter adapter;
    private ScanEngine scanEngine;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private boolean isScanning = false;
    private int totalSelectedCount = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        currentTheme = prefs.getInt(KEY_THEME, THEME_LIGHT);
        applyTheme();
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initViews();
        setupTabs();
        setupScanButton();
        setupSettings();
        setupRamAndCache();
        checkPermissions();
        updateStorageInfo();
        updateStatsDisplay();
        refreshStorageData();
    }

    private void initViews() {
        // Pages
        pageScan = findViewById(R.id.pageScan);
        pageResults = findViewById(R.id.pageResults);
        pageSettings = findViewById(R.id.pageSettings);
        pageStorage = findViewById(R.id.pageStorage);

        // Tabs
        tabScan = findViewById(R.id.tabScan);
        tabResults = findViewById(R.id.tabResults);
        tabSettings = findViewById(R.id.tabSettings);
        tabStorage = findViewById(R.id.tabStorage);
        tabScanIcon = findViewById(R.id.tabScanIcon);
        tabResultsIcon = findViewById(R.id.tabResultsIcon);
        tabSettingsIcon = findViewById(R.id.tabSettingsIcon);
        tabStorageIcon = findViewById(R.id.tabStorageIcon);
        tabScanLabel = findViewById(R.id.tabScanLabel);
        tabResultsLabel = findViewById(R.id.tabResultsLabel);
        tabSettingsLabel = findViewById(R.id.tabSettingsLabel);
        tabStorageLabel = findViewById(R.id.tabStorageLabel);

        // Scan page
        scanButton = findViewById(R.id.scanButton);
        View scanCard = findViewById(R.id.scanCard);
        scanTitle = findViewById(R.id.scanTitle);
        scanSubtitle = findViewById(R.id.scanSubtitle);
        scanProgress = findViewById(R.id.scanProgress);
        scanStatus = findViewById(R.id.scanStatus);
        statsTotalValue = findViewById(R.id.statsTotalValue);
        statsItemsValue = findViewById(R.id.statsItemsValue);
        statsCleanedValue = findViewById(R.id.statsCleanedValue);
        storageUsedLabel = findViewById(R.id.storageUsedLabel);
        storageFreeLabel = findViewById(R.id.storageFreeLabel);
        storageTotalLabel = findViewById(R.id.storageTotalLabel);
        tipText = findViewById(R.id.tipText);

        // Results page
        resultsList = findViewById(R.id.resultsList);
        resultsSummarySize = findViewById(R.id.resultsSummarySize);
        btnSelectAll = findViewById(R.id.btnSelectAll);
        btnCleanSelected = findViewById(R.id.btnCleanSelected);
        bottomActionBar = findViewById(R.id.bottomActionBar);
        resultsHeader = findViewById(R.id.resultsHeader);

        // Settings page
        themeLight = findViewById(R.id.themeLight);
        themeDark = findViewById(R.id.themeDark);
        themeSystem = findViewById(R.id.themeSystem);
        chkDeepScan = findViewById(R.id.chkDeepScan);
        chkIncludeMedia = findViewById(R.id.chkIncludeMedia);
        btnManagePermissions = findViewById(R.id.btnManagePermissions);

        // Storage page views
        storageBarInternal = findViewById(R.id.storageBarInternal);
        storageUsedLabelInternal = findViewById(R.id.storageUsedLabelInternal);
        storageFreeLabelInternal = findViewById(R.id.storageFreeLabelInternal);
        storageTotalLabelInternal = findViewById(R.id.storageTotalLabelInternal);
        storageBarSd = findViewById(R.id.storageBarSd);
        storageUsedLabelSd = findViewById(R.id.storageUsedLabelSd);
        storageFreeLabelSd = findViewById(R.id.storageFreeLabelSd);
        storageTotalLabelSd = findViewById(R.id.storageTotalLabelSd);
        sdCardSection = findViewById(R.id.sdCardSection);
        spaceApps = findViewById(R.id.spaceApps);
        spaceMedia = findViewById(R.id.spaceMedia);
        spaceCache = findViewById(R.id.spaceCache);
        spaceOther = findViewById(R.id.spaceOther);
        ramBar = findViewById(R.id.ramBar);
        ramUsedLabel = findViewById(R.id.ramUsedLabel);
        ramFreeLabel = findViewById(R.id.ramFreeLabel);
        ramTotalLabel = findViewById(R.id.ramTotalLabel);
        ramProcessCount = findViewById(R.id.ramProcessCount);
        appCacheSize = findViewById(R.id.appCacheSize);
        btnCleanRam = findViewById(R.id.btnCleanRam);
        btnCleanAppCache = findViewById(R.id.btnCleanAppCache);
        deviceModel = findViewById(R.id.deviceModel);
        deviceAndroid = findViewById(R.id.deviceAndroid);
        deviceCpu = findViewById(R.id.deviceCpu);
        deviceScreen = findViewById(R.id.deviceScreen);
        batteryBar = findViewById(R.id.batteryBar);
        batteryLevel = findViewById(R.id.batteryLevel);
        batteryStatus = findViewById(R.id.batteryStatus);
        batteryTemp = findViewById(R.id.batteryTemp);
        batteryHealth = findViewById(R.id.batteryHealth);
        btnBoost = findViewById(R.id.btnBoost);
        btnOpenAppManager = findViewById(R.id.btnOpenAppManager);
        btnScanDup = findViewById(R.id.btnScanDup);
        btnScanWhatsapp = findViewById(R.id.btnScanWhatsapp);
        btnExportReport = findViewById(R.id.btnExportReport);
        dupStatus = findViewById(R.id.dupStatus);
        whatsappStatus = findViewById(R.id.whatsappStatus);
        chkSchedule = findViewById(R.id.chkSchedule);
        scheduleInterval = findViewById(R.id.scheduleInterval);

        // Init data
        categories = new ArrayList<>();
        adapter = new JunkAdapter(this, categories);
        adapter.setListener(new JunkAdapter.JunkAdapterListener() {
            @Override
            public void onCategoryClick(int categoryIndex) {
                JunkCategory cat = categories.get(categoryIndex);
                cat.expanded = !cat.expanded;
                adapter.notifyCategoriesChanged();
                updateResultsSummary();
            }

            @Override
            public void onFileChecked(int categoryIndex, int fileIndex, boolean checked) {
                updateResultsSummary();
            }

            @Override
            public void onSelectionChanged() {
                updateResultsSummary();
            }
        });
        resultsList.setAdapter(adapter);

        // Load settings
        chkDeepScan.setChecked(prefs.getBoolean(KEY_DEEP_SCAN, false));
        chkIncludeMedia.setChecked(prefs.getBoolean(KEY_INCLUDE_MEDIA, false));
    }

    private void setupTabs() {
        tabScan.setOnClickListener(v -> switchTab(0));
        tabResults.setOnClickListener(v -> switchTab(1));
        tabStorage.setOnClickListener(v -> { if (needsStorageRefresh) { refreshStorageData(); needsStorageRefresh = false; } switchTab(3); });
        tabSettings.setOnClickListener(v -> switchTab(2));
    }

    private void switchTab(int index) {
        pageScan.setVisibility(index == 0 ? View.VISIBLE : View.GONE);
        pageResults.setVisibility(index == 1 ? View.VISIBLE : View.GONE);
        pageStorage.setVisibility(index == 3 ? View.VISIBLE : View.GONE);
        pageSettings.setVisibility(index == 2 ? View.VISIBLE : View.GONE);

        int activeColor = currentTheme == THEME_DARK ? 0xFF4A9AF5 : 0xFF1A73E8;
        int inactiveColor = currentTheme == THEME_DARK ? 0xFF6B6B80 : 0xFF9CA3AF;

        tabScanIcon.setColorFilter(index == 0 ? activeColor : inactiveColor);
        tabScanLabel.setTextColor(index == 0 ? activeColor : inactiveColor);

        tabResultsIcon.setColorFilter(index == 1 ? activeColor : inactiveColor);
        tabResultsLabel.setTextColor(index == 1 ? activeColor : inactiveColor);

        tabStorageIcon.setColorFilter(index == 3 ? activeColor : inactiveColor);
        tabStorageLabel.setTextColor(index == 3 ? activeColor : inactiveColor);

        tabSettingsIcon.setColorFilter(index == 2 ? activeColor : inactiveColor);
        tabSettingsLabel.setTextColor(index == 2 ? activeColor : inactiveColor);

        if (index == 1) updateResultsSummary();
        if (index == 2) updateThemeButtons();
        if (index == 3) { needsStorageRefresh = false; }
    }

    private void setupScanButton() {
        View.OnClickListener scanClick = v -> {
            if (isScanning) {
                if (scanEngine != null) scanEngine.cancel();
                scanTitle.setText("Cancelado");
                return;
            }
            if (!hasStoragePermission()) {
                scanTitle.setText("Sem permissão");
                showPermissionDialog();
                return;
            }
            scanTitle.setText("Permission OK!");
            startScan();
        };
        scanButton.setOnClickListener(scanClick);
        findViewById(R.id.scanCard).setOnClickListener(scanClick);
    }

    private boolean hasStoragePermission() {
        if (Build.VERSION.SDK_INT >= 30) {
            return Environment.isExternalStorageManager();
        } else {
            return checkSelfPermission(android.Manifest.permission.READ_EXTERNAL_STORAGE)
                    == PackageManager.PERMISSION_GRANTED;
        }
    }

    private void checkPermissions() {
        if (!hasStoragePermission()) {
            showPermissionDialog();
        }
    }

    private void showPermissionDialog() {
        if (Build.VERSION.SDK_INT >= 30) {
            new AlertDialog.Builder(this)
                .setTitle("Permissão de Gerenciamento")
                .setMessage("Para uma limpeza completa, conceda acesso a Todos os Arquivos nas configurações.")
                .setPositiveButton("Abrir Configurações", (d, w) -> {
                    Intent intent = new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION);
                    intent.setData(Uri.parse("package:" + getPackageName()));
                    startActivityForResult(intent, REQUEST_MANAGE_STORAGE);
                })
                .setNegativeButton("Cancelar", null)
                .show();
        } else if (Build.VERSION.SDK_INT >= 23) {
            requestPermissions(
                new String[]{android.Manifest.permission.READ_EXTERNAL_STORAGE,
                             android.Manifest.permission.WRITE_EXTERNAL_STORAGE},
                100);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == 100) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                updateStorageInfo();
            } else {
                Toast.makeText(this, "Permissão necessária para escanear arquivos", Toast.LENGTH_LONG).show();
            }
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_MANAGE_STORAGE) {
            if (hasStoragePermission()) {
                updateStorageInfo();
                Toast.makeText(this, "Permissão concedida!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "Permissão não concedida", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private void startScan() {
        Toast.makeText(this, "Iniciando scan…", Toast.LENGTH_SHORT).show();
        isScanning = true;
        scanProgress.setVisibility(View.VISIBLE);
        scanProgress.setProgress(0);
        scanTitle.setText("Escaneando…");
        scanSubtitle.setText("Aguarde enquanto analisamos seu dispositivo");
        scanButton.setEnabled(false);
        scanButton.setAlpha(0.6f);
        tipText.setText("Escaneando arquivos… pode levar alguns segundos.");

        categories.clear();
        adapter.notifyDataSetChanged();
        bottomActionBar.setVisibility(View.GONE);
        updateStatsDisplay();

        boolean deepScan = chkDeepScan.isChecked();
        boolean includeMedia = chkIncludeMedia.isChecked();

        // Detect SD card paths
        List<String> sdPaths = new ArrayList<>();
        List<StorageUtil.VolumeInfo> vols = StorageUtil.getAllVolumes(this);
        String internalPath = Environment.getExternalStorageDirectory().getAbsolutePath();
        for (StorageUtil.VolumeInfo vol : vols) {
            if (!vol.isPrimary) {
                sdPaths.add(vol.path);
            }
        }

        scanEngine = new ScanEngine(new ScanEngine.ScanListener() {
            @Override
            public void onProgress(int percent, String status) {
                mainHandler.post(() -> {
                    scanProgress.setProgress(percent);
                    scanStatus.setText(status);
                });
            }

            @Override
            public void onComplete(List<JunkCategory> result, long totalSize) {
                mainHandler.post(() -> {
                    categories.clear();
                    categories.addAll(result);
                    adapter.notifyDataSetChanged();

                    totalJunkSize = totalSize;
                    totalJunkItems = 0;
                    for (JunkCategory cat : categories) {
                        totalJunkItems += cat.getItemCount();
                    }

                    isScanning = false;
                    scanProgress.setVisibility(View.GONE);
                    scanTitle.setText("Escaneamento Concluído!");
                    scanSubtitle.setText("Toque para escanear novamente");
                    scanButton.setEnabled(true);
                    scanButton.setAlpha(1f);

                    updateStatsDisplay();
                    updateStorageInfo();
                    needsStorageRefresh = true;

                    if (categories.isEmpty()) {
                        tipText.setText("Nenhum arquivo de lixo encontrado! Seu dispositivo está limpo.");
                    } else {
                        tipText.setText(totalJunkItems + " itens encontrados! Vá em Resultados para revisar.");
                    }

                    // Auto-switch to results
                    if (!categories.isEmpty()) {
                        switchTab(1);
                    }
                });
            }

            @Override
            public void onError(String message) {
                mainHandler.post(() -> {
                    isScanning = false;
                    scanProgress.setVisibility(View.GONE);
                    scanTitle.setText("Erro");
                    scanSubtitle.setText("Toque para tentar novamente");
                    scanButton.setEnabled(true);
                    scanButton.setAlpha(1f);
                    tipText.setText(message);
                });
            }
        }, deepScan, includeMedia, sdPaths);
        scanEngine.start();
    }

    private long totalJunkSize = 0;
    private int totalJunkItems = 0;
    private boolean needsStorageRefresh = true;

    private void refreshStorageData() {
        // Storage volumes
        List<StorageUtil.VolumeInfo> vols = StorageUtil.getAllVolumes(this);
        boolean foundSd = false;

        for (StorageUtil.VolumeInfo vol : vols) {
            if (vol.isPrimary) {
                storageBarInternal.setProgress(vol.getUsedPercent());
                storageUsedLabelInternal.setText("Usado: " + FileUtils.formatSize(vol.getUsedBytes()));
                storageFreeLabelInternal.setText("Livre: " + FileUtils.formatSize(vol.freeBytes));
                storageTotalLabelInternal.setText("Total: " + FileUtils.formatSize(vol.totalBytes));
            } else {
                foundSd = true;
                sdCardSection.setVisibility(View.VISIBLE);
                storageBarSd.setProgress(vol.getUsedPercent());
                storageUsedLabelSd.setText("Usado: " + FileUtils.formatSize(vol.getUsedBytes()));
                storageFreeLabelSd.setText("Livre: " + FileUtils.formatSize(vol.freeBytes));
                storageTotalLabelSd.setText("Total: " + FileUtils.formatSize(vol.totalBytes));
            }
        }

        if (!foundSd) {
            sdCardSection.setVisibility(View.GONE);
        }

        // RAM info
        RamManager.RamInfo ram = RamManager.getRamInfo(this);
        ramBar.setProgress(ram.getUsedPercent());
        ramUsedLabel.setText("Usado: " + FileUtils.formatSize(ram.usedRam));
        ramFreeLabel.setText("Livre: " + FileUtils.formatSize(ram.availableRam));
        ramTotalLabel.setText("Total: " + FileUtils.formatSize(ram.totalRam));
        ramProcessCount.setText(RamManager.getRunningProcessCount(this) + " processos");

        // App cache info
        long cacheSize = RamManager.getAppCacheSize(this);
        appCacheSize.setText("Cache: " + FileUtils.formatSize(cacheSize));

        // Storage summary from scan results
        if (categories != null && !categories.isEmpty()) {
            for (JunkCategory cat : categories) {
                if (cat.type == JunkItem.TYPE_CACHE) {
                    spaceCache.setText("• Cache: " + FileUtils.formatSize(cat.getTotalSize()));
                }
            }
        }

        // Device Info
        DeviceInfo.DeviceData dev = DeviceInfo.getDeviceData(this);
        deviceModel.setText("• Modelo: " + dev.manufacturer + " " + dev.model);
        deviceAndroid.setText("• Android: " + dev.androidVersion + " (API " + dev.sdkInt + ")");
        deviceCpu.setText("• CPU: " + dev.cpu + " (" + dev.cores + " núcleos)");
        deviceScreen.setText("• Tela: " + dev.resolution + " (" + String.format("%.1f", dev.density) + "x)");

        // Battery Info
        BatteryInfo.BatteryData bat = BatteryInfo.getBatteryData(this);
        batteryBar.setProgress(bat.getPercent());
        batteryLevel.setText("Nível: " + bat.getPercent() + "%");
        batteryStatus.setText(bat.getStatusStr());
        batteryTemp.setText("Temperatura: " + String.format("%.1f", bat.getTempCelsius()) + "°C" + " (" + bat.voltage + "mV)");
        batteryHealth.setText("Saúde: " + bat.getHealthStr() + " (" + (bat.technology != null ? bat.technology : "N/A") + ")");
    }

    private void setupRamAndCache() {
        btnCleanRam.setOnClickListener(v -> {
            btnCleanRam.setEnabled(false);
            btnCleanRam.setText("Limpando RAM…");
            new Thread(() -> {
                long freed = RamManager.cleanRam(this);
                mainHandler.post(() -> {
                    refreshStorageData();
                    btnCleanRam.setEnabled(true);
                    btnCleanRam.setText("Limpar RAM");
                    Toast.makeText(this, "RAM limpa: " + FileUtils.formatSize(freed) + " liberados", Toast.LENGTH_SHORT).show();
                });
            }).start();
        });

        btnCleanAppCache.setOnClickListener(v -> {
            btnCleanAppCache.setEnabled(false);
            btnCleanAppCache.setText("Limpando Cache…");
            new Thread(() -> {
                long freed = RamManager.cleanAppCache(this);
                mainHandler.post(() -> {
                    refreshStorageData();
                    btnCleanAppCache.setEnabled(true);
                    btnCleanAppCache.setText("Limpar Cache do App");
                    Toast.makeText(this, "Cache limpo: " + FileUtils.formatSize(freed) + " liberados", Toast.LENGTH_SHORT).show();
                });
            }).start();
        });

        // Boost 1-Tap
        btnBoost.setOnClickListener(v -> {
            btnBoost.setEnabled(false);
            btnBoost.setText("Otimizando…");
            new Thread(() -> {
                long ramFreed = RamManager.cleanRam(this);
                long cacheFreed = RamManager.cleanAppCache(this);
                mainHandler.post(() -> {
                    refreshStorageData();
                    btnBoost.setEnabled(true);
                    btnBoost.setText("Boost!");
                    Toast.makeText(this, "Boost: RAM " + FileUtils.formatSize(ramFreed) + " + Cache " + FileUtils.formatSize(cacheFreed), Toast.LENGTH_SHORT).show();
                    switchTab(0);
                    startScan();
                });
            }).start();
        });

        // App Manager
        btnOpenAppManager.setOnClickListener(v -> showAppManager());

        // Duplicate Scanner
        btnScanDup.setOnClickListener(v -> {
            btnScanDup.setEnabled(false);
            btnScanDup.setText("Escaneando…");
            dupStatus.setText("Escaneando arquivos duplicados…");
            new Thread(() -> {
                final java.util.List<DuplicateScanner.DuplicateGroup> dups =
                    DuplicateScanner.findDuplicates(android.os.Environment.getExternalStorageDirectory(), true);
                mainHandler.post(() -> {
                    btnScanDup.setEnabled(true);
                    btnScanDup.setText("Escanear Duplicatas");
                    if (dups.isEmpty()) {
                        dupStatus.setText("Nenhum arquivo duplicado encontrado.");
                    } else {
                        long wasted = DuplicateScanner.getTotalWasted(dups);
                        dupStatus.setText(dups.size() + " grupos de duplicatas encontrados! (" + FileUtils.formatSize(wasted) + " desperdiçados)");
                        showDuplicateResults(dups);
                    }
                });
            }).start();
        });

        // WhatsApp Cleaner
        btnScanWhatsapp.setOnClickListener(v -> {
            btnScanWhatsapp.setEnabled(false);
            btnScanWhatsapp.setText("Escaneando…");
            whatsappStatus.setText("Escaneando mídia do WhatsApp…");
            new Thread(() -> {
                final java.util.List<WhatsAppCleaner.WhatsAppItem> items = WhatsAppCleaner.scanOldMedia();
                mainHandler.post(() -> {
                    btnScanWhatsapp.setEnabled(true);
                    btnScanWhatsapp.setText("Escanear WhatsApp");
                    if (items.isEmpty()) {
                        whatsappStatus.setText("Nenhuma mídia WhatsApp encontrada para limpeza.");
                    } else {
                        long total = WhatsAppCleaner.getTotalSize(items);
                        whatsappStatus.setText(items.size() + " arquivos encontrados (" + FileUtils.formatSize(total) + ")");
                        showWhatsAppResults(items);
                    }
                });
            }).start();
        });

        // Export Report
        btnExportReport.setOnClickListener(v -> {
            if (categories == null || categories.isEmpty()) {
                Toast.makeText(this, "Nenhum resultado para exportar. Escaneie primeiro.", Toast.LENGTH_SHORT).show();
                return;
            }
            new Thread(() -> {
                File file = ReportExporter.exportReport(this, categories);
                mainHandler.post(() -> {
                    if (file != null) {
                        Toast.makeText(this, "Relatório salvo em: " + file.getAbsolutePath(), Toast.LENGTH_LONG).show();
                    } else {
                        Toast.makeText(this, "Erro ao exportar relatório.", Toast.LENGTH_SHORT).show();
                    }
                });
            }).start();
        });

        // Scheduling
        chkSchedule.setOnCheckedChangeListener((b, checked) -> {
            if (checked) {
                try {
                    int hours = Integer.parseInt(scheduleInterval.getText().toString());
                    if (hours < 1) hours = 24;
                    ScheduleManager.scheduleClean(this, hours);
                    Toast.makeText(this, "Limpeza agendada a cada " + hours + " horas.", Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    chkSchedule.setChecked(false);
                    Toast.makeText(this, "Intervalo inválido.", Toast.LENGTH_SHORT).show();
                }
            } else {
                ScheduleManager.cancelSchedule(this);
                Toast.makeText(this, "Limpeza agendada cancelada.", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void showAppManager() {
        new Thread(() -> {
            final java.util.List<AppManager.AppInfo> apps = AppManager.getInstalledApps(MainActivity.this, false);
            mainHandler.post(() -> {
                if (apps.isEmpty()) {
                    Toast.makeText(MainActivity.this, "Nenhum app encontrado.", Toast.LENGTH_SHORT).show();
                    return;
                }
                String[] items = new String[Math.min(apps.size(), 50)];
                for (int i = 0; i < items.length; i++) {
                    AppManager.AppInfo a = apps.get(i);
                    items[i] = a.appName + " (" + FileUtils.formatSize(a.apkSize) + ")";
                }
                new AlertDialog.Builder(MainActivity.this)
                    .setTitle("Apps Instalados (" + apps.size() + ")")
                    .setItems(items, (d, w) -> {
                        if (w < apps.size()) {
                            final AppManager.AppInfo selected = apps.get(w);
                            String[] opts = {"Desinstalar", "Extrair APK", "Cancelar"};
                            new AlertDialog.Builder(MainActivity.this)
                                .setTitle(selected.appName)
                                .setItems(opts, (d2, w2) -> {
                                    if (w2 == 0) {
                                        AppManager.uninstallApp(MainActivity.this, selected.packageName);
                                    } else if (w2 == 1) {
                                        new Thread(() -> {
                                            File outDir = new File(Environment.getExternalStorageDirectory(), "CellCleaner/APKs");
                                            File apk = AppManager.extractApk(MainActivity.this, selected.packageName, outDir);
                                            mainHandler.post(() -> {
                                                if (apk != null) {
                                                    Toast.makeText(MainActivity.this, "APK salvo em: " + apk.getAbsolutePath(), Toast.LENGTH_LONG).show();
                                                } else {
                                                    Toast.makeText(MainActivity.this, "Erro ao extrair APK.", Toast.LENGTH_SHORT).show();
                                                }
                                            });
                                        }).start();
                                    }
                                }).show();
                        }
                    })
                    .setNegativeButton("Fechar", null)
                    .show();
            });
        }).start();
    }

    private void showDuplicateResults(final java.util.List<DuplicateScanner.DuplicateGroup> dups) {
        mainHandler.post(() -> {
            StringBuilder sb = new StringBuilder();
            int shown = 0;
            for (DuplicateScanner.DuplicateGroup g : dups) {
                if (shown >= 10) break;
                sb.append(g.files.get(0).getName()).append(" (").append(FileUtils.formatSize(g.fileSize)).append(") x").append(g.files.size()).append("\n");
                shown++;
            }
            if (dups.size() > 10) sb.append("… e mais ").append(dups.size() - 10).append(" grupos.");
            new AlertDialog.Builder(MainActivity.this)
                .setTitle("Arquivos Duplicados")
                .setMessage(sb.toString())
                .setPositiveButton("OK", null)
                .show();
        });
    }

    private void showWhatsAppResults(final java.util.List<WhatsAppCleaner.WhatsAppItem> items) {
        long total = WhatsAppCleaner.getTotalSize(items);
        new AlertDialog.Builder(MainActivity.this)
            .setTitle("Mídia WhatsApp Enviada")
            .setMessage(items.size() + " arquivos encontrados.\nTamanho total: " + FileUtils.formatSize(total) +
                       "\n\nDeseja excluir toda essa mídia enviada?\n(Ela já foi enviada e ocupa espaço desnecessário.)")
            .setPositiveButton("Limpar Tudo", (d, w) -> {
                new Thread(() -> {
                    int deleted = 0;
                    long freed = 0;
                    for (WhatsAppCleaner.WhatsAppItem item : items) {
                        if (FileUtils.deleteFile(item.file)) {
                            deleted++;
                            freed += item.size;
                        }
                    }
                    final int fd = deleted;
                    final long ff = freed;
                    mainHandler.post(() -> {
                        whatsappStatus.setText(fd + " arquivos removidos (" + FileUtils.formatSize(ff) + ")");
                        Toast.makeText(MainActivity.this, "WhatsApp limpo: " + fd + " arquivos (" + FileUtils.formatSize(ff) + ")", Toast.LENGTH_LONG).show();
                    });
                }).start();
            })
            .setNegativeButton("Cancelar", null)
            .show();
    }

    private void updateStatsDisplay() {
        if (isScanning) {
            statsTotalValue.setText("…");
            statsItemsValue.setText("…");
            statsCleanedValue.setText("…");
        } else {
            statsTotalValue.setText(FileUtils.formatSize(totalJunkSize));
            statsItemsValue.setText(String.valueOf(totalJunkItems));
            statsCleanedValue.setText(FileUtils.formatSize(ScanEngine.getFreeStorage()));
        }
    }

    private void updateStorageInfo() {
        storageUsedLabel.setText(FileUtils.formatSize(ScanEngine.getUsedStorage()));
        storageFreeLabel.setText(FileUtils.formatSize(ScanEngine.getFreeStorage()));
        storageTotalLabel.setText(FileUtils.formatSize(ScanEngine.getTotalStorage()));
    }

    private void updateResultsSummary() {
        int totalItems = 0;
        int selectedItems = 0;
        long selectedSize = 0;

        for (JunkCategory cat : categories) {
            totalItems += cat.getItemCount();
            selectedItems += cat.getSelectedCount();
            selectedSize += cat.getSelectedSize();
        }

        resultsSummarySize.setText(selectedItems + " de " + totalItems + " itens • " +
                                   FileUtils.formatSize(selectedSize));

        if (selectedItems > 0) {
            bottomActionBar.setVisibility(View.VISIBLE);
            btnCleanSelected.setText("Limpar " + selectedItems + " itens (" +
                                     FileUtils.formatSize(selectedSize) + ")");
        } else {
            bottomActionBar.setVisibility(View.GONE);
        }
    }

    public void setupResultsActions() {
        btnSelectAll.setOnClickListener(v -> {
            boolean allSelected = true;
            for (JunkCategory cat : categories) {
                for (JunkItem item : cat.items) {
                    if (!item.selected) { allSelected = false; break; }
                }
            }
            for (JunkCategory cat : categories) {
                cat.selectAll(!allSelected);
            }
            adapter.notifyDataSetChanged();
            updateResultsSummary();
        });

        btnCleanSelected.setOnClickListener(v -> {
            int selectedCount = 0;
            for (JunkCategory cat : categories) {
                selectedCount += cat.getSelectedCount();
            }
            if (selectedCount == 0) {
                Toast.makeText(this, "Nenhum item selecionado", Toast.LENGTH_SHORT).show();
                return;
            }

            new AlertDialog.Builder(this)
                .setTitle("Confirmar Limpeza")
                .setMessage("Tem certeza que deseja excluir " + selectedCount + " itens? Esta ação não pode ser desfeita.")
                .setPositiveButton("Sim, Limpar", (d, w) -> executeClean())
                .setNegativeButton("Cancelar", null)
                .show();
        });
    }

    private void executeClean() {
        btnCleanSelected.setEnabled(false);
        btnCleanSelected.setText("Limpando…");

        new Thread(() -> {
            int deleted = 0;
            long freed = 0;

            for (JunkCategory cat : categories) {
                List<JunkItem> toRemove = new ArrayList<>();
                for (JunkItem item : cat.items) {
                    if (item.selected) {
                        if (FileUtils.deleteFile(item.file)) {
                            freed += item.getSize();
                            deleted++;
                            toRemove.add(item);
                        }
                    }
                }
                cat.items.removeAll(toRemove);
            }

            // Remove empty categories
            List<JunkCategory> emptyCats = new ArrayList<>();
            for (JunkCategory cat : categories) {
                if (cat.getItemCount() == 0) emptyCats.add(cat);
            }
            categories.removeAll(emptyCats);

            final int finalDeleted = deleted;
            final long finalFreed = freed;

            mainHandler.post(() -> {
                totalJunkSize -= finalFreed;
                totalJunkItems -= finalDeleted;

                adapter.notifyDataSetChanged();
                updateStatsDisplay();
                updateStorageInfo();
                updateResultsSummary();

                btnCleanSelected.setEnabled(true);
                btnCleanSelected.setText("Limpar");

                if (categories.isEmpty()) {
                    bottomActionBar.setVisibility(View.GONE);
                }

                Toast.makeText(this, finalDeleted + " itens removidos (" +
                               FileUtils.formatSize(finalFreed) + ")", Toast.LENGTH_LONG).show();

                if (finalDeleted > 0) {
                    tipText.setText(finalDeleted + " itens limpos! " +
                                   FileUtils.formatSize(finalFreed) + " liberados.");
                }
            });
        }).start();
    }

    // ========== SETTINGS ==========

    private void setupSettings() {
        setupResultsActions();

        themeLight.setOnClickListener(v -> setAppTheme(THEME_LIGHT));
        themeDark.setOnClickListener(v -> setAppTheme(THEME_DARK));
        themeSystem.setOnClickListener(v -> setAppTheme(THEME_SYSTEM));

        updateThemeButtons();

        chkDeepScan.setOnCheckedChangeListener((b, checked) -> {
            prefs.edit().putBoolean(KEY_DEEP_SCAN, checked).apply();
        });

        chkIncludeMedia.setOnCheckedChangeListener((b, checked) -> {
            prefs.edit().putBoolean(KEY_INCLUDE_MEDIA, checked).apply();
        });

        btnManagePermissions.setOnClickListener(v -> showPermissionDialog());
    }

    private void setAppTheme(int theme) {
        currentTheme = theme;
        prefs.edit().putInt(KEY_THEME, theme).apply();
        recreate();
    }

    private void applyTheme() {
        switch (currentTheme) {
            case THEME_DARK:
                setTheme(android.R.style.Theme_Material_NoActionBar);
                break;
            case THEME_LIGHT:
            default:
                setTheme(android.R.style.Theme_Material_Light_NoActionBar);
                break;
        }
    }

    private void updateThemeButtons() {
        int activeColor = 0xFF1A73E8;
        int inactiveBg = 0xFFF5F7FA;
        int activeTextColor = 0xFFFFFFFF;
        int inactiveTextColor = 0xFF6B7280;

        if (currentTheme == THEME_DARK) {
            activeColor = 0xFF4A9AF5;
            inactiveBg = 0xFF1E1E2E;
            inactiveTextColor = 0xFF9E9EB0;
        }

        themeLight.setBackgroundDrawable(getResources().getDrawable(
            currentTheme == THEME_LIGHT ? R.drawable.bg_button_primary : R.drawable.bg_card_light));
        themeLight.setTextColor(currentTheme == THEME_LIGHT ? activeTextColor : inactiveTextColor);

        themeDark.setBackgroundDrawable(getResources().getDrawable(
            currentTheme == THEME_DARK ? R.drawable.bg_button_primary : R.drawable.bg_card_light));
        themeDark.setTextColor(currentTheme == THEME_DARK ? activeTextColor : inactiveTextColor);

        themeSystem.setBackgroundDrawable(getResources().getDrawable(
            currentTheme == THEME_SYSTEM ? R.drawable.bg_button_primary : R.drawable.bg_card_light));
        themeSystem.setTextColor(currentTheme == THEME_SYSTEM ? activeTextColor : inactiveTextColor);
    }

    @Override
    protected void onDestroy() {
        if (scanEngine != null) {
            scanEngine.cancel();
        }
        super.onDestroy();
    }
}
