package com.cleaner.app;

public class JunkItem {
    public String name;
    public String path;
    public long size;
    public String category;
    public boolean isSelected;

    public JunkItem(String name, String path, long size, String category) {
        this.name = name;
        this.path = path;
        this.size = size;
        this.category = category;
        this.isSelected = true;
    }
}
