package com.biblia.estudo.data;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import com.biblia.estudo.model.Highlight;

import java.util.ArrayList;
import java.util.List;

public class HighlightDao {

    private SQLiteDatabase db;

    public HighlightDao(SQLiteDatabase db) {
        this.db = db;
    }

    public long insert(Highlight h) {
        ContentValues cv = new ContentValues();
        cv.put("book_id", h.getBookId());
        cv.put("chapter", h.getChapter());
        cv.put("verse_start", h.getVerseStart());
        cv.put("verse_end", h.getVerseEnd());
        cv.put("color", h.getColor());
        cv.put("created_at", System.currentTimeMillis());
        return db.insert(BibleDatabaseHelper.TABLE_HIGHLIGHTS, null, cv);
    }

    public void deleteByVerse(long bookId, int chapter, int verse) {
        db.delete(BibleDatabaseHelper.TABLE_HIGHLIGHTS,
                "book_id=? AND chapter=? AND verse_start<=? AND verse_end>=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter),
                        String.valueOf(verse), String.valueOf(verse)});
    }

    public List<Highlight> getByChapter(long bookId, int chapter) {
        List<Highlight> list = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_HIGHLIGHTS, null,
                "book_id=? AND chapter=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter)},
                null, null, "verse_start ASC");
        if (c != null) {
            while (c.moveToNext()) list.add(cursorTo(c));
            c.close();
        }
        return list;
    }

    public boolean isHighlighted(long bookId, int chapter, int verse) {
        Cursor c = db.rawQuery("SELECT COUNT(*) FROM " + BibleDatabaseHelper.TABLE_HIGHLIGHTS +
                " WHERE book_id=? AND chapter=? AND verse_start<=? AND verse_end>=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter),
                        String.valueOf(verse), String.valueOf(verse)});
        boolean exists = false;
        if (c != null && c.moveToFirst()) { exists = c.getInt(0) > 0; c.close(); }
        return exists;
    }

    private Highlight cursorTo(Cursor c) {
        Highlight h = new Highlight();
        h.setId(c.getLong(c.getColumnIndexOrThrow("_id")));
        h.setBookId(c.getLong(c.getColumnIndexOrThrow("book_id")));
        h.setChapter(c.getInt(c.getColumnIndexOrThrow("chapter")));
        h.setVerseStart(c.getInt(c.getColumnIndexOrThrow("verse_start")));
        h.setVerseEnd(c.getInt(c.getColumnIndexOrThrow("verse_end")));
        h.setColor(c.getString(c.getColumnIndexOrThrow("color")));
        h.setCreatedAt(c.getLong(c.getColumnIndexOrThrow("created_at")));
        return h;
    }
}
