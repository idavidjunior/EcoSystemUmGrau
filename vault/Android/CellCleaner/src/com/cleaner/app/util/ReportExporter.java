package com.cleaner.app.util;

import android.content.Context;
import android.os.Environment;

import com.cleaner.app.model.JunkCategory;

import java.io.File;
import java.io.FileWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class ReportExporter {

    public static File exportReport(Context context, List<JunkCategory> categories) {
        try {
            File dir = new File(Environment.getExternalStorageDirectory(), "CellCleaner");
            if (!dir.exists()) dir.mkdirs();
            String timestamp = new SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", Locale.getDefault()).format(new Date());
            File file = new File(dir, "relatorio_" + timestamp + ".txt");

            FileWriter fw = new FileWriter(file);
            fw.write("═══════════════════════════════════════════\n");
            fw.write("  Cell Cleaner - Relatório de Varredura\n");
            fw.write("  Data: " + new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(new Date()) + "\n");
            fw.write("═══════════════════════════════════════════\n\n");

            if (categories == null || categories.isEmpty()) {
                fw.write("Nenhum item encontrado.\n");
            } else {
                long total = 0;
                for (JunkCategory cat : categories) {
                    fw.write("▶ " + cat.name + "\n");
                    fw.write("   Itens: " + cat.getItemCount() + "\n");
                    fw.write("   Tamanho: " + FileUtils.formatSize(cat.getTotalSize()) + "\n");
                    if (cat.items != null) {
                        for (int i = 0; i < cat.items.size(); i++) {
                            fw.write("   " + (i+1) + ". " + cat.items.get(i).file.getAbsolutePath()
                                   + " (" + FileUtils.formatSize(cat.items.get(i).getSize()) + ")\n");
                        }
                    }
                    fw.write("\n");
                    total += cat.getTotalSize();
                }
                fw.write("═══════════════════════════════════════════\n");
                fw.write("  TOTAL: " + FileUtils.formatSize(total) + "\n");
            }
            fw.close();
            return file;
        } catch (Exception e) { return null; }
    }
}