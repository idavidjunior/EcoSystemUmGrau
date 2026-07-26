package com.cleaner.app.model;

import java.util.ArrayList;
import java.util.List;

public class JunkCategory {
    public int type;
    public String name;
    public String iconName;
    public List<JunkItem> items;
    public boolean expanded;

    public JunkCategory(int type, String name, String iconName) {
        this.type = type;
        this.name = name;
        this.iconName = iconName;
        this.items = new ArrayList<>();
        this.expanded = false;
    }

    public int getItemCount() {
        return items.size();
    }

    public long getTotalSize() {
        long total = 0;
        for (JunkItem item : items) {
            total += item.getSize();
        }
        return total;
    }

    public int getSelectedCount() {
        int count = 0;
        for (JunkItem item : items) {
            if (item.selected) count++;
        }
        return count;
    }

    public long getSelectedSize() {
        long total = 0;
        for (JunkItem item : items) {
            if (item.selected) total += item.getSize();
        }
        return total;
    }

    public void toggleSelectAll() {
        boolean hasUnselected = false;
        for (JunkItem item : items) {
            if (!item.selected) { hasUnselected = true; break; }
        }
        for (JunkItem item : items) {
            item.selected = hasUnselected;
        }
    }

    public void selectAll(boolean select) {
        for (JunkItem item : items) {
            item.selected = select;
        }
    }
}
