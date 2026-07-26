package com.cleaner.app.util;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class WhatsAppCleaner {

    public static class WhatsAppItem {
        public File file;
        public String type;
        public long size;
        public WhatsAppItem(File f, String t) { this.file = f; this.type = t; this.size = f.length(); }
    }

    public static List<WhatsAppItem> scanOldMedia() {
        List<WhatsAppItem> items = new ArrayList<>();
        String[] paths = {
            "/sdcard/WhatsApp/Media/WhatsApp Images/Sent",
            "/sdcard/WhatsApp/Media/WhatsApp Video/Sent",
            "/sdcard/WhatsApp/Media/WhatsApp Audio/Sent",
            "/sdcard/WhatsApp/Media/WhatsApp Documents/Sent",
            "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Images/Sent",
            "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Video/Sent",
            "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Audio/Sent",
            "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Documents/Sent",
        };
        for (String path : paths) {
            File dir = new File(path);
            if (dir.exists() && dir.isDirectory()) {
                File[] files = dir.listFiles();
                if (files != null) {
                    for (File f : files) {
                        if (f.isFile()) {
                            String type = path.contains("Images") ? "Imagem" :
                                          path.contains("Video") ? "Vídeo" :
                                          path.contains("Audio") ? "Áudio" : "Documento";
                            items.add(new WhatsAppItem(f, type));
                        }
                    }
                }
            }
        }
        return items;
    }

    public static long getTotalSize(List<WhatsAppItem> items) {
        long s = 0;
        for (WhatsAppItem i : items) s += i.size;
        return s;
    }
}