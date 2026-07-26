package com.biblia.estudo.ui.library;

import android.app.Activity;
import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.Spinner;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.data.BookDao;
import com.biblia.estudo.model.Book;
import com.biblia.estudo.ui.apocrypha.ApocryphaBookListActivity;
import com.biblia.estudo.ui.bible.BibleReaderActivity;
import com.biblia.estudo.utils.NavigationHelper;

import java.util.List;

public class LibraryActivity extends Activity {

    private EditText searchView;
    private ListView listView;
    private Spinner testamentSpinner;
    private BookDao bookDao;
    private BookListAdapter adapter;
    private int currentTestament = Book.TESTAMENT_OLD;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_library);

        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getBibleDatabase();
        bookDao = new BookDao(db);

        searchView = findViewById(R.id.searchView);
        listView = findViewById(R.id.listView);
        testamentSpinner = findViewById(R.id.testamentSpinner);

        NavigationHelper.setupBottomNav(this);
        setupSpinner();
        setupSearch();
        loadBooks(currentTestament);
    }

    private void setupSpinner() {
        String[] options = {"Antigo Testamento", "Novo Testamento", "Apócrifos (Deuterocanônicos)", "Narrativas Apócrifas"};
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, options);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        testamentSpinner.setAdapter(adapter);

        testamentSpinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                switch (position) {
                    case 0:
                        currentTestament = Book.TESTAMENT_OLD;
                        loadBooks(currentTestament);
                        break;
                    case 1:
                        currentTestament = Book.TESTAMENT_NEW;
                        loadBooks(currentTestament);
                        break;
                    case 2:
                        currentTestament = Book.TESTAMENT_APOCRYPHA;
                        loadBooks(currentTestament);
                        break;
                    case 3:
                        startActivity(new Intent(LibraryActivity.this, ApocryphaBookListActivity.class));
                        break;
                }
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {}
        });
    }

    private void setupSearch() {
        searchView.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}
            @Override
            public void afterTextChanged(Editable s) {
                String query = s.toString().trim();
                if (query.isEmpty()) {
                    loadBooks(currentTestament);
                } else {
                    List<Book> results = bookDao.searchByName(query);
                    adapter = new BookListAdapter(LibraryActivity.this, results);
                    listView.setAdapter(adapter);
                }
            }
        });
    }

    private void loadBooks(int testament) {
        currentTestament = testament;
        List<Book> books = bookDao.getByTestament(testament);
        adapter = new BookListAdapter(this, books);
        listView.setAdapter(adapter);

        listView.setOnItemClickListener((parent, view, position, id) -> {
            Book book = adapter.getItem(position);
            Intent intent = new Intent(LibraryActivity.this, BibleReaderActivity.class);
            intent.putExtra("book_id", book.getId());
            intent.putExtra("book_name", book.getName());
            intent.putExtra("chapter_count", book.getChapterCount());
            startActivity(intent);
        });
    }
}
