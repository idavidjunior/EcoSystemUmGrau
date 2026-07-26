package com.biblia.estudo.ui.study;

import android.app.Activity;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;

import java.util.ArrayList;
import java.util.List;

public class TopicIndexActivity extends Activity {

    private EditText searchField;
    private ListView topicsList;
    private LayoutInflater inflater;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_topic_index);
        inflater = LayoutInflater.from(this);

        searchField = findViewById(R.id.searchField);
        topicsList = findViewById(R.id.topicsList);

        searchField.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}
            @Override
            public void afterTextChanged(Editable s) {
                loadTopics(s.toString().trim());
            }
        });

        loadTopics("");
    }

    private void loadTopics(String query) {
        final List<TopicItem> topics = new ArrayList<>();
        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getTopicIndexDatabase();
        Cursor c;

        if (query.isEmpty()) {
            c = db.rawQuery("SELECT _id, name, description FROM topics ORDER BY name ASC LIMIT 200", null);
        } else {
            c = db.rawQuery("SELECT _id, name, description FROM topics WHERE name LIKE ? ORDER BY name ASC LIMIT 200",
                    new String[]{"%" + query + "%"});
        }

        while (c.moveToNext()) {
            TopicItem item = new TopicItem();
            item.name = c.getString(c.getColumnIndexOrThrow("name"));
            item.description = c.getString(c.getColumnIndexOrThrow("description"));
            topics.add(item);
        }
        c.close();

        topicsList.setAdapter(new BaseAdapter() {
            @Override public int getCount() { return topics.size(); }
            @Override public Object getItem(int pos) { return topics.get(pos); }
            @Override public long getItemId(int pos) { return pos; }
            @Override
            public View getView(int pos, View convertView, ViewGroup parent) {
                if (convertView == null) {
                    convertView = inflater.inflate(R.layout.list_item_topic, parent, false);
                }
                TopicItem t = topics.get(pos);
                ((TextView) convertView.findViewById(R.id.topicName)).setText(t.name);
                String desc = t.description;
                if (desc != null && desc.length() > 80) desc = desc.substring(0, 80) + "...";
                ((TextView) convertView.findViewById(R.id.topicCount)).setText(desc);
                return convertView;
            }
        });
    }

    static class TopicItem {
        String name;
        String description;
    }
}
