package com.biblia.estudo.ui.search;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.os.Bundle;
import android.os.Handler;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.AdapterView;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.RadioButton;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.ui.bible.BibleReaderActivity;
import com.biblia.estudo.utils.SearchEngine;

public class SearchActivity extends Activity {

    private EditText searchInput;
    private ListView resultsList;
    private TextView noResults;
    private SearchEngine searchEngine;
    private SearchResultsAdapter adapter;
    private Handler searchHandler = new Handler();
    private Runnable searchRunnable;

    private int searchMode = 0;
    private RadioButton searchWord, searchPhrase, searchBook, searchTopic;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_search);

        searchEngine = new SearchEngine(BibliaApplication.getDatabaseManager());

        searchInput = findViewById(R.id.searchInput);
        resultsList = findViewById(R.id.resultsList);
        noResults = findViewById(R.id.noResults);
        searchWord = findViewById(R.id.searchWord);
        searchPhrase = findViewById(R.id.searchPhrase);
        searchBook = findViewById(R.id.searchBook);
        searchTopic = findViewById(R.id.searchTopic);

        setupTabs();
        setupSearchInput();
    }

    private void setupTabs() {
        View.OnClickListener l = v -> {
            RadioButton[] tabs = {searchWord, searchPhrase, searchBook, searchTopic};
            for (int i = 0; i < tabs.length; i++) {
                boolean selected = tabs[i] == v;
                tabs[i].setChecked(selected);
                if (selected) {
                    searchMode = i;
                    tabs[i].setTextColor(getResources().getColor(R.color.accent));
                } else {
                    tabs[i].setTextColor(getResources().getColor(R.color.text_secondary));
                }
            }
            String q = searchInput.getText().toString().trim();
            if (q.length() >= 2) performSearch(q);
        };
        searchWord.setOnClickListener(l);
        searchPhrase.setOnClickListener(l);
        searchBook.setOnClickListener(l);
        searchTopic.setOnClickListener(l);
    }

    private void setupSearchInput() {
        searchInput.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                if (searchRunnable != null) searchHandler.removeCallbacks(searchRunnable);
            }

            @Override
            public void afterTextChanged(Editable s) {
                String query = s.toString().trim();
                if (query.length() < 2) {
                    resultsList.setVisibility(View.GONE);
                    noResults.setVisibility(View.GONE);
                    return;
                }
                searchRunnable = () -> performSearch(query);
                searchHandler.postDelayed(searchRunnable, 300);
            }
        });
    }

    private void performSearch(String query) {
        Cursor cursor = null;
        switch (searchMode) {
            case 0:
            case 1:
                cursor = searchEngine.searchByWordCursor(query);
                break;
            case 2:
                cursor = searchEngine.searchByBookCursor(query);
                break;
            case 3:
                cursor = searchEngine.searchByTopic(query);
                break;
        }

        if (cursor != null && cursor.getCount() > 0) {
            noResults.setVisibility(View.GONE);
            resultsList.setVisibility(View.VISIBLE);
            adapter = new SearchResultsAdapter(this, cursor);
            resultsList.setAdapter(adapter);

            resultsList.setOnItemClickListener((parent, view, position, id) -> {
                Cursor c = (Cursor) adapter.getItem(position);
                long bookId = c.getLong(c.getColumnIndexOrThrow("book_id"));
                int chapter = c.getInt(c.getColumnIndexOrThrow("chapter"));
                int verse = c.getInt(c.getColumnIndexOrThrow("verse_number"));
                String bookName = c.getString(c.getColumnIndexOrThrow("book_name"));

                Intent intent = new Intent(SearchActivity.this, BibleReaderActivity.class);
                intent.putExtra("book_id", bookId);
                intent.putExtra("book_name", bookName);
                intent.putExtra("chapter_count", 150);
                intent.putExtra("chapter", chapter);
                intent.putExtra("verse", verse);
                startActivity(intent);
            });
        } else {
            noResults.setVisibility(View.VISIBLE);
            resultsList.setVisibility(View.GONE);
        }
    }
}
