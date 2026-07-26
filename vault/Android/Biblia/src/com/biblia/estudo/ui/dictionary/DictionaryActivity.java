package com.biblia.estudo.ui.dictionary;

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

public class DictionaryActivity extends Activity {

    private EditText searchField;
    private ListView resultsList;
    private TextView detailView;
    private LayoutInflater inflater;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_dictionary);
        inflater = LayoutInflater.from(this);

        searchField = findViewById(R.id.searchField);
        resultsList = findViewById(R.id.resultsList);
        detailView = findViewById(R.id.detailView);

        setupSearch();
    }

    private void setupSearch() {
        searchField.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}

            @Override
            public void afterTextChanged(Editable s) {
                String query = s.toString().trim();
                if (query.length() >= 2) {
                    searchDictionary(query);
                }
            }
        });

        resultsList.setOnItemClickListener((parent, view, position, id) -> {
            DictItem item = (DictItem) parent.getItemAtPosition(position);
            StringBuilder detail = new StringBuilder();
            detail.append(item.word).append("\n\n");
            detail.append(item.definition).append("\n\n");
            detailView.setText(detail.toString());
            detailView.setVisibility(View.VISIBLE);
            resultsList.setVisibility(View.GONE);
        });
    }

    private void searchDictionary(String query) {
        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getDictionaryDatabase();
        Cursor c = db.rawQuery(
                "SELECT _id, word, definition FROM dictionary WHERE word LIKE ? ORDER BY word LIMIT 50",
                new String[]{"%" + query + "%"});

        final List<DictItem> items = new ArrayList<>();
        while (c.moveToNext()) {
            DictItem item = new DictItem();
            item.word = c.getString(c.getColumnIndexOrThrow("word"));
            item.definition = c.getString(c.getColumnIndexOrThrow("definition"));
            items.add(item);
        }
        c.close();

        resultsList.setAdapter(new BaseAdapter() {
            @Override public int getCount() { return items.size(); }
            @Override public Object getItem(int pos) { return items.get(pos); }
            @Override public long getItemId(int pos) { return pos; }
            @Override
            public View getView(int pos, View convertView, ViewGroup parent) {
                if (convertView == null) {
                    convertView = inflater.inflate(R.layout.list_item_dictionary, parent, false);
                }
                DictItem item = items.get(pos);
                ((TextView) convertView.findViewById(R.id.dictWord)).setText(item.word);
                String def = item.definition;
                if (def != null && def.length() > 80) def = def.substring(0, 80) + "...";
                ((TextView) convertView.findViewById(R.id.dictDefinition)).setText(def);
                return convertView;
            }
        });
        resultsList.setVisibility(View.VISIBLE);
        detailView.setVisibility(View.GONE);
    }

    static class DictItem {
        String word;
        String definition;
    }
}
