package com.cleaner.app.model;

import com.cleaner.app.util.FileUtils;
import java.io.File;

public class JunkItem {
    public static final int TYPE_CACHE = 0;
    public static final int TYPE_TEMP = 1;
    public static final int TYPE_APK = 2;
    public static final int TYPE_LOG = 3;
    public static final int TYPE_EMPTY_DIR = 4;
    public static final int TYPE_LARGE_FILE = 5;
    public static final int TYPE_DOWNLOAD = 6;

    public File file;
    public int type;
    public boolean selected;

    public JunkItem(File file, int type) {
        this.file = file;
        this.type = type;
        this.selected = true;
    }

    public long getSize() {
        return file.isDirectory() ? FileUtils.getDirectorySize(file) : file.length();
    }

    public String getDisplayName() {
        String name = file.getName();
        if (name.isEmpty()) name = file.getAbsolutePath();
        return name;
    }

    public boolean isDirectory() {
        return file.isDirectory();
    }

    public static String getTypeName(int type) {
        switch (type) {
            case TYPE_CACHE: return "cache";
            case TYPE_TEMP: return "temp";
            case TYPE_APK: return "apk";
            case TYPE_LOG: return "log";
            case TYPE_EMPTY_DIR: return "empty";
            case TYPE_LARGE_FILE: return "large";
            case TYPE_DOWNLOAD: return "download";
            default: return "unknown";
        }
    }
}
