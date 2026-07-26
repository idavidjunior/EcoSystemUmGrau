package com.biblia.estudo.ui.library;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.model.UserResource;

import java.util.List;

public class ResourceListAdapter extends BaseAdapter {

    private Context context;
    private List<UserResource> resources;

    public ResourceListAdapter(Context context, List<UserResource> resources) {
        this.context = context;
        this.resources = resources;
    }

    @Override
    public int getCount() { return resources.size(); }

    @Override
    public UserResource getItem(int position) { return resources.get(position); }

    @Override
    public long getItemId(int position) { return resources.get(position).getId(); }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        if (convertView == null) {
            convertView = LayoutInflater.from(context).inflate(
                    android.R.layout.simple_list_item_2, parent, false);
        }

        UserResource res = getItem(position);
        TextView title = convertView.findViewById(android.R.id.text1);
        TextView subtitle = convertView.findViewById(android.R.id.text2);

        String icon = getIcon(res.getFileTypeLabel());
        title.setText(icon + "  " + res.getTitle());
        subtitle.setText(res.getFileTypeLabel() + "  •  " + formatSize(res.getSize()));

        return convertView;
    }

    private String getIcon(String type) {
        switch (type) {
            case "PDF": return "\uD83D\uDCC4";
            case "DOC": return "\uD83D\uDCDD";
            case "XLS": return "\uD83D\uDCCA";
            case "PPT": return "\uD83D\uDCC8";
            case "TXT": return "\uD83D\uDCDD";
            case "IMG": return "\uD83D\uDDBC";
            default: return "\uD83D\uDCC1";
        }
    }

    private String formatSize(long bytes) {
        if (bytes <= 0) return "";
        String[] units = {"B", "KB", "MB"};
        int u = 0;
        double s = bytes;
        while (s >= 1024 && u < units.length - 1) { s /= 1024; u++; }
        return String.format("%.1f %s", s, units[u]);
    }
}
