package com.cleaner.app.adapter;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.CheckBox;
import android.widget.ImageView;
import android.widget.TextView;

import com.cleaner.app.R;
import com.cleaner.app.model.JunkCategory;
import com.cleaner.app.model.JunkItem;
import com.cleaner.app.util.FileUtils;

import java.util.List;

public class JunkAdapter extends BaseAdapter {

    private static final int VIEW_TYPE_CATEGORY = 0;
    private static final int VIEW_TYPE_FILE = 1;

    private final Context context;
    private final List<JunkCategory> categories;
    private final LayoutInflater inflater;
    private JunkAdapterListener listener;

    public interface JunkAdapterListener {
        void onCategoryClick(int categoryIndex);
        void onFileChecked(int categoryIndex, int fileIndex, boolean checked);
        void onSelectionChanged();
    }

    public JunkAdapter(Context context, List<JunkCategory> categories) {
        this.context = context;
        this.categories = categories;
        this.inflater = LayoutInflater.from(context);
    }

    public void setListener(JunkAdapterListener listener) {
        this.listener = listener;
    }

    @Override
    public int getCount() {
        int count = 0;
        for (JunkCategory cat : categories) {
            count++; // category header
            if (cat.expanded) {
                count += cat.getItemCount();
            }
        }
        return count;
    }

    @Override
    public int getViewTypeCount() {
        return 2;
    }

    @Override
    public int getItemViewType(int position) {
        int[] pos = getPositionInfo(position);
        return pos[1] == -1 ? VIEW_TYPE_CATEGORY : VIEW_TYPE_FILE;
    }

    @Override
    public Object getItem(int position) {
        int[] pos = getPositionInfo(position);
        if (pos[1] == -1) {
            return categories.get(pos[0]);
        }
        return categories.get(pos[0]).items.get(pos[1]);
    }

    @Override
    public long getItemId(int position) {
        return position;
    }

    private int[] getPositionInfo(int position) {
        int count = 0;
        for (int i = 0; i < categories.size(); i++) {
            if (count == position) return new int[]{i, -1};
            count++;
            JunkCategory cat = categories.get(i);
            if (cat.expanded) {
                for (int j = 0; j < cat.getItemCount(); j++) {
                    if (count == position) return new int[]{i, j};
                    count++;
                }
            }
        }
        return new int[]{-1, -1};
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        int[] pos = getPositionInfo(position);
        if (pos[0] < 0) return convertView;

        if (pos[1] == -1) {
            return getCategoryView(pos[0], convertView, parent);
        }
        return getFileView(pos[0], pos[1], convertView, parent);
    }

    private View getCategoryView(int catIndex, View convertView, ViewGroup parent) {
        ViewHolderCategory holder;
        if (convertView == null || convertView.getTag() == null ||
            !(convertView.getTag() instanceof ViewHolderCategory)) {
            convertView = inflater.inflate(R.layout.item_junk_category, parent, false);
            holder = new ViewHolderCategory();
            holder.iconContainer = convertView.findViewById(R.id.categoryIconContainer);
            holder.icon = convertView.findViewById(R.id.categoryIcon);
            holder.name = convertView.findViewById(R.id.categoryName);
            holder.count = convertView.findViewById(R.id.categoryCount);
            holder.size = convertView.findViewById(R.id.categorySize);
            holder.arrow = convertView.findViewById(R.id.categoryArrow);
            convertView.setTag(holder);
        } else {
            holder = (ViewHolderCategory) convertView.getTag();
        }

        JunkCategory cat = categories.get(catIndex);

        // Set icon based on type
        int iconRes = getIconForType(cat.type);
        int iconBgColor = getColorForType(cat.type);
        holder.icon.setImageResource(iconRes);
        holder.icon.setColorFilter(0xFFFFFFFF);
        holder.iconContainer.setBackgroundColor(iconBgColor);

        holder.name.setText(cat.name);
        holder.count.setText(cat.getItemCount() + " itens");
        holder.size.setText(FileUtils.formatSize(cat.getTotalSize()));

        // Arrow indicator
        if (cat.expanded) {
            holder.arrow.setVisibility(View.VISIBLE);
            holder.arrow.setImageResource(android.R.drawable.arrow_up_float);
            holder.arrow.setColorFilter(0xFF6B7280);
        } else {
            holder.arrow.setVisibility(View.VISIBLE);
            holder.arrow.setImageResource(android.R.drawable.arrow_down_float);
            holder.arrow.setColorFilter(0xFF6B7280);
        }

        final int index = catIndex;
        convertView.setOnClickListener(v -> {
            if (listener != null) listener.onCategoryClick(index);
        });

        return convertView;
    }

    private View getFileView(int catIndex, int fileIndex, View convertView, ViewGroup parent) {
        ViewHolderFile holder;
        if (convertView == null || convertView.getTag() == null ||
            !(convertView.getTag() instanceof ViewHolderFile)) {
            convertView = inflater.inflate(R.layout.item_junk_file, parent, false);
            holder = new ViewHolderFile();
            holder.row = convertView.findViewById(R.id.fileRow);
            holder.checkbox = convertView.findViewById(R.id.fileCheckbox);
            holder.name = convertView.findViewById(R.id.fileName);
            holder.path = convertView.findViewById(R.id.filePath);
            holder.size = convertView.findViewById(R.id.fileSize);
            convertView.setTag(holder);
        } else {
            holder = (ViewHolderFile) convertView.getTag();
        }

        JunkItem item = categories.get(catIndex).items.get(fileIndex);

        holder.name.setText(item.getDisplayName());
        holder.path.setText(item.file.getParent());
        holder.size.setText(FileUtils.formatSize(item.getSize()));
        holder.checkbox.setChecked(item.selected);

        // Alternate row colors
        holder.row.setBackgroundColor(fileIndex % 2 == 0 ?
            0xFFF9FAFB : 0xFFFFFFFF);

        final int ci = catIndex;
        final int fi = fileIndex;

        holder.checkbox.setOnCheckedChangeListener(null);
        holder.checkbox.setChecked(item.selected);
        holder.checkbox.setOnCheckedChangeListener((buttonView, isChecked) -> {
            item.selected = isChecked;
            if (listener != null) listener.onFileChecked(ci, fi, isChecked);
        });

        holder.row.setOnClickListener(v -> {
            boolean newState = !item.selected;
            item.selected = newState;
            holder.checkbox.setChecked(newState);
            if (listener != null) listener.onFileChecked(ci, fi, newState);
        });

        return convertView;
    }

    private int getIconForType(int type) {
        switch (type) {
            case JunkItem.TYPE_CACHE: return R.drawable.ic_cache;
            case JunkItem.TYPE_TEMP: return R.drawable.ic_temp;
            case JunkItem.TYPE_APK: return R.drawable.ic_apk;
            case JunkItem.TYPE_LOG: return R.drawable.ic_log;
            case JunkItem.TYPE_EMPTY_DIR: return R.drawable.ic_folder;
            case JunkItem.TYPE_LARGE_FILE: return R.drawable.ic_storage;
            default: return R.drawable.ic_storage;
        }
    }

    private int getColorForType(int type) {
        switch (type) {
            case JunkItem.TYPE_CACHE: return 0xFFFF6D00;
            case JunkItem.TYPE_TEMP: return 0xFFF4511E;
            case JunkItem.TYPE_APK: return 0xFFE53935;
            case JunkItem.TYPE_LOG: return 0xFF8E24AA;
            case JunkItem.TYPE_EMPTY_DIR: return 0xFF3949AB;
            case JunkItem.TYPE_LARGE_FILE: return 0xFF00897B;
            default: return 0xFF1A73E8;
        }
    }

    public void notifyCategoriesChanged() {
        notifyDataSetChanged();
    }

    static class ViewHolderCategory {
        View iconContainer;
        ImageView icon;
        TextView name;
        TextView count;
        TextView size;
        ImageView arrow;
    }

    static class ViewHolderFile {
        View row;
        CheckBox checkbox;
        TextView name;
        TextView path;
        TextView size;
    }
}
