package com.biblia.estudo.ui.study;

import android.app.Activity;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.utils.NavigationHelper;

public class StudyCommentaryActivity extends Activity {

    private TextView verseTitle;
    private TextView commentaryContent;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_commentary);

        NavigationHelper.setupBackButton(this);

        long bookId = getIntent().getLongExtra("book_id", 0);
        String bookName = getIntent().getStringExtra("book_name");
        int chapter = getIntent().getIntExtra("chapter", 1);
        int verse = getIntent().getIntExtra("verse", 1);

        verseTitle = findViewById(R.id.verseTitle);
        commentaryContent = findViewById(R.id.commentaryContent);

        verseTitle.setText(bookName + " " + chapter + ":" + verse);

        loadCommentary(bookId, chapter, verse);
    }

    private void loadCommentary(long bookId, int chapter, int verse) {
        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getCommentaryDatabase();
        Cursor c = db.rawQuery(
                "SELECT content, author FROM commentaries WHERE book_id=? AND chapter=? AND " +
                        "(verse_start=0 OR (verse_start<=? AND (verse_end=0 OR verse_end>=?))) " +
                        "ORDER BY verse_start ASC LIMIT 10",
                new String[]{String.valueOf(bookId), String.valueOf(chapter),
                        String.valueOf(verse), String.valueOf(verse)});

        StringBuilder sb = new StringBuilder();
        if (c != null) {
            while (c.moveToNext()) {
                String content = c.getString(0);
                String author = c.getString(1);
                if (author != null && !author.isEmpty()) {
                    sb.append("\n\n— ").append(author);
                }
                sb.append(content).append("\n\n");
            }
            c.close();
        }

        if (sb.length() == 0) {
            sb.append("Nenhum comentário disponível para este versículo.");
        }

        commentaryContent.setText(sb.toString());
    }
}
