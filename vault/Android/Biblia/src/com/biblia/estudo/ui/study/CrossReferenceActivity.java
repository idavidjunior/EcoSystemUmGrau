package com.biblia.estudo.ui.study;

import android.app.Activity;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ListView;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.utils.NavigationHelper;

import java.util.ArrayList;
import java.util.List;

public class CrossReferenceActivity extends Activity {

    private TextView verseRef;
    private ListView refsList;
    private LayoutInflater inflater;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_cross_reference);
        inflater = LayoutInflater.from(this);

        NavigationHelper.setupBackButton(this);

        long bookId = getIntent().getLongExtra("book_id", 0);
        String bookName = getIntent().getStringExtra("book_name");
        int chapter = getIntent().getIntExtra("chapter", 1);
        int verse = getIntent().getIntExtra("verse", 1);

        verseRef = findViewById(R.id.verseRef);
        refsList = findViewById(R.id.refsList);

        verseRef.setText(bookName + " " + chapter + ":" + verse);

        loadCrossReferences(bookId, chapter, verse);
    }

    private void loadCrossReferences(long bookId, int chapter, int verse) {
        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getCrossReferenceDatabase();
        Cursor c = db.rawQuery(
                "SELECT cr._id, cr.target_book_name, cr.target_chapter, cr.target_verse " +
                        "FROM cross_references cr WHERE cr.source_book_id=? AND " +
                        "cr.source_chapter=? AND cr.source_verse=? " +
                        "ORDER BY cr.target_book_name, cr.target_chapter, cr.target_verse",
                new String[]{String.valueOf(bookId), String.valueOf(chapter), String.valueOf(verse)});

        final List<String> refs = new ArrayList<>();
        while (c.moveToNext()) {
            String ref = c.getString(c.getColumnIndexOrThrow("target_book_name")) + " " +
                    c.getInt(c.getColumnIndexOrThrow("target_chapter")) + ":" +
                    c.getInt(c.getColumnIndexOrThrow("target_verse"));
            refs.add(ref);
        }
        c.close();

        refsList.setAdapter(new BaseAdapter() {
            @Override public int getCount() { return refs.size(); }
            @Override public Object getItem(int pos) { return refs.get(pos); }
            @Override public long getItemId(int pos) { return pos; }
            @Override
            public View getView(int pos, View convertView, ViewGroup parent) {
                if (convertView == null) {
                    convertView = inflater.inflate(R.layout.list_item_cross_ref, parent, false);
                }
                ((TextView) convertView.findViewById(R.id.refText)).setText(refs.get(pos));
                return convertView;
            }
        });
    }
}
