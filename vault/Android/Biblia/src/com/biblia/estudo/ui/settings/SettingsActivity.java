package com.biblia.estudo.ui.settings;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.app.ThemeManager;
import com.biblia.estudo.utils.BackupManager;

import java.util.ArrayList;
import java.util.List;

public class SettingsActivity extends Activity {

    private ListView settingsList;
    private SettingsAdapter adapter;
    private ThemeManager themeManager;
    private LayoutInflater inflater;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        themeManager = BibliaApplication.getThemeManager();
        themeManager.applyTheme(this);
        setContentView(R.layout.activity_settings);
        inflater = LayoutInflater.from(this);

        settingsList = findViewById(R.id.settingsRecycler);
        adapter = new SettingsAdapter();
        settingsList.setAdapter(adapter);

        settingsList.setOnItemClickListener((parent, view, position, id) -> {
            switch (position) {
                case 0: showThemeDialog(); break;
                case 1: showFontSizeDialog(); break;
                case 2: showFontFamilyDialog(); break;
                case 3: showLineSpacingDialog(); break;
                case 9: exportBackup(); break;
                case 10: importBackup(); break;
            }
        });
    }

    private void showThemeDialog() {
        String[] themes = {"Claro", "Escuro", "Sépia", "Preto AMOLED", "Branco (Papel)"};
        int current = themeManager.getCurrentTheme();
        new AlertDialog.Builder(this)
                .setTitle(R.string.settings_theme)
                .setSingleChoiceItems(themes, current, (dialog, which) -> {
                    themeManager.setTheme(which);
                    dialog.dismiss();
                    recreate();
                })
                .show();
    }

    private void showFontSizeDialog() {
        String[] sizes = {"14", "16", "18", "20", "22", "24", "28", "32", "36"};
        int current = themeManager.getFontSize();
        int idx = java.util.Arrays.asList(sizes).indexOf(String.valueOf(current));
        new AlertDialog.Builder(this)
                .setTitle(R.string.settings_font_size)
                .setSingleChoiceItems(new String[]{"Muito Pequeno", "Pequeno", "Médio", "Grande", "Muito Grande",
                        "Extra Grande", "Enorme", "Gigante", "Máximo"},
                        idx >= 0 ? idx : 1, (dialog, which) -> {
                            themeManager.setFontSize(Integer.parseInt(sizes[which]));
                            dialog.dismiss();
                        })
                .show();
    }

    private void showFontFamilyDialog() {
        String[] families = {getString(R.string.settings_font_serif), getString(R.string.settings_font_sans_serif)};
        new AlertDialog.Builder(this)
                .setTitle(R.string.settings_font_family)
                .setSingleChoiceItems(families, themeManager.getFontFamily(), (dialog, which) -> {
                    themeManager.setFontFamily(which);
                    dialog.dismiss();
                })
                .show();
    }

    private void showLineSpacingDialog() {
        new AlertDialog.Builder(this)
                .setTitle(R.string.settings_line_spacing)
                .setSingleChoiceItems(new String[]{"Compacto", "Normal", "Confortável", "Amplo", "Muito Amplo"}, 1,
                        (dialog, which) -> {
                            float[] spacings = {1.0f, 1.2f, 1.5f, 1.8f, 2.0f};
                            themeManager.setLineSpacing(spacings[which]);
                            dialog.dismiss();
                        })
                .show();
    }

    private void exportBackup() {
        try {
            BackupManager bm = new BackupManager(this);
            String path = bm.exportToJson();
            Toast.makeText(this, "Backup criado: " + path, Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "Erro ao criar backup: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void importBackup() {
        Toast.makeText(this, "Selecione o arquivo de backup", Toast.LENGTH_SHORT).show();
    }

    class SettingsAdapter extends BaseAdapter {
        private List<SettingsItem> items;
        private String[] icons = {"☀", "A", "A", "¶", "#", "📝", "💬", "🔗", "↕", "💾", "📂"};

        SettingsAdapter() {
            items = new ArrayList<>();
            items.add(new SettingsItem("Tema", "Claro / Escuro / Sépia / AMOLED", true));
            items.add(new SettingsItem("Tamanho da Fonte", String.valueOf(themeManager.getFontSize()) + "sp", true));
            items.add(new SettingsItem("Família da Fonte", themeManager.getFontFamily() == 0 ? "Com Serifa" : "Sem Serifa", true));
            items.add(new SettingsItem("Espaçamento", String.valueOf(themeManager.getLineSpacing()), true));
            items.add(new SettingsItem("Mostrar Números dos Versículos", themeManager.showVerseNumbers() ? "Sim" : "Não", false));
            items.add(new SettingsItem("Mostrar Notas", themeManager.showNotes() ? "Sim" : "Não", false));
            items.add(new SettingsItem("Mostrar Comentários", themeManager.showCommentaries() ? "Sim" : "Não", false));
            items.add(new SettingsItem("Mostrar Referências Cruzadas", themeManager.showCrossReferences() ? "Sim" : "Não", false));
            items.add(new SettingsItem("Modo de Rolagem", themeManager.getScrollMode() == 0 ? "Contínua" : "Por Capítulo", false));
            items.add(new SettingsItem("Exportar Backup", "Salvar configurações e notas", true));
            items.add(new SettingsItem("Importar Backup", "Restaurar de arquivo", true));
        }

        @Override public int getCount() { return items.size(); }
        @Override public Object getItem(int pos) { return items.get(pos); }
        @Override public long getItemId(int pos) { return pos; }

        @Override
        public View getView(int pos, View convertView, ViewGroup parent) {
            if (convertView == null) {
                convertView = inflater.inflate(R.layout.list_item_settings, parent, false);
            }
            SettingsItem item = items.get(pos);
            ((TextView) convertView.findViewById(R.id.settingsIcon)).setText(icons[pos]);
            ((TextView) convertView.findViewById(R.id.settingsTitle)).setText(item.title);
            return convertView;
        }
    }

    class SettingsItem {
        String title, subtitle;
        boolean clickable;
        SettingsItem(String t, String s, boolean c) { title = t; subtitle = s; clickable = c; }
    }
}
