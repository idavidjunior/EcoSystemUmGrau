package com.biblia.estudo.ui.notes;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.data.BookDao;
import com.biblia.estudo.data.NoteDao;
import com.biblia.estudo.model.Book;
import com.biblia.estudo.model.UserNote;
import com.biblia.estudo.ui.bible.BibleReaderActivity;

import java.util.List;

public class NotesActivity extends Activity {

    private ListView notesList;
    private TextView emptyView;
    private NoteDao noteDao;
    private BookDao bookDao;
    private NotesAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_notes);

        notesList = findViewById(R.id.notesList);
        emptyView = findViewById(R.id.emptyView);

        noteDao = new NoteDao(BibliaApplication.getDatabaseManager().getBibleDatabase());
        bookDao = new BookDao(BibliaApplication.getDatabaseManager().getBibleDatabase());

        loadNotes();
    }

    private void loadNotes() {
        List<UserNote> notes = noteDao.getAll();
        if (notes.isEmpty()) {
            emptyView.setVisibility(View.VISIBLE);
            notesList.setVisibility(View.GONE);
        } else {
            emptyView.setVisibility(View.GONE);
            notesList.setVisibility(View.VISIBLE);
            adapter = new NotesAdapter(this, notes);
            notesList.setAdapter(adapter);

            notesList.setOnItemClickListener(new AdapterView.OnItemClickListener() {
                @Override
                public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                    UserNote note = adapter.getItem(position);
                    Book book = bookDao.getById(note.getBookId());
                    String bookName = book != null ? book.getName() : "Livro";

                    Intent intent = new Intent(NotesActivity.this, BibleReaderActivity.class);
                    intent.putExtra("book_id", note.getBookId());
                    intent.putExtra("book_name", bookName);
                    intent.putExtra("chapter", note.getChapter());
                    intent.putExtra("verse", note.getVerseNumber());
                    startActivity(intent);
                }
            });
        }
    }
}
