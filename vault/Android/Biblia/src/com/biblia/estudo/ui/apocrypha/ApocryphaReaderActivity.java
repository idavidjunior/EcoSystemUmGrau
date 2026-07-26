package com.biblia.estudo.ui.apocrypha;

import android.app.Activity;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.text.method.ScrollingMovementMethod;
import android.view.View;
import android.widget.ScrollView;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.utils.NavigationHelper;

import java.util.ArrayList;
import java.util.List;

public class ApocryphaReaderActivity extends Activity {

    private TextView chapterTitle;
    private TextView chapterContent;
    private TextView toolbarTitle;
    private ScrollView scrollView;
    private View btnPrev, btnNext;

    private long bookId;
    private String bookName;
    private List<Chapter> chapters = new ArrayList<>();
    private int currentChapterIndex = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_apocrypha_reader);

        bookId = getIntent().getLongExtra("book_id", 0);
        bookName = getIntent().getStringExtra("book_name");

        chapterTitle = findViewById(R.id.chapterTitle);
        chapterContent = findViewById(R.id.chapterContent);
        toolbarTitle = findViewById(R.id.toolbarTitle);
        scrollView = findViewById(R.id.scrollView);
        btnPrev = findViewById(R.id.btnPrev);
        btnNext = findViewById(R.id.btnNext);

        if (toolbarTitle != null) {
            toolbarTitle.setText(bookName != null ? bookName : "Narrativas Apócrifas");
        }

        chapterContent.setMovementMethod(new ScrollingMovementMethod());
        NavigationHelper.setupBottomNav(this);

        loadChapters();

        btnPrev.setOnClickListener(v -> {
            if (currentChapterIndex > 0) {
                currentChapterIndex--;
                showChapter(currentChapterIndex);
            }
        });

        btnNext.setOnClickListener(v -> {
            if (currentChapterIndex < chapters.size() - 1) {
                currentChapterIndex++;
                showChapter(currentChapterIndex);
            }
        });
    }

    private void loadChapters() {
        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getBibleDatabase();
        Cursor c = db.rawQuery(
            "SELECT _id, chapter_number, title, content FROM apocrypha_chapters WHERE book_id=? ORDER BY chapter_number",
            new String[]{String.valueOf(bookId)});
        chapters.clear();
        while (c.moveToNext()) {
            Chapter ch = new Chapter();
            ch.id = c.getLong(0);
            ch.number = c.getInt(1);
            ch.title = c.getString(2);
            ch.content = c.getString(3);
            chapters.add(ch);
        }
        c.close();

        if (!chapters.isEmpty()) {
            showChapter(0);
        }
    }

    private void showChapter(int index) {
        Chapter ch = chapters.get(index);
        chapterTitle.setText(ch.title);
        chapterContent.setText(ch.content);
        scrollView.scrollTo(0, 0);

        btnPrev.setEnabled(index > 0);
        btnPrev.setAlpha(index > 0 ? 1f : 0.3f);
        btnNext.setEnabled(index < chapters.size() - 1);
        btnNext.setAlpha(index < chapters.size() - 1 ? 1f : 0.3f);
    }

    static class Chapter {
        long id;
        int number;
        String title;
        String content;
    }
}
