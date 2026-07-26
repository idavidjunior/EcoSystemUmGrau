package com.biblia.estudo.data;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import com.biblia.estudo.model.ReadingProgress;

import java.util.Date;

public class ReadingProgressDao {

    private SQLiteDatabase db;

    public ReadingProgressDao(SQLiteDatabase db) {
        this.db = db;
    }

    public void saveProgress(long bookId, int chapter, int verse) {
        ContentValues cv = new ContentValues();
        cv.put("book_id", bookId);
        cv.put("chapter", chapter);
        cv.put("verse", verse);
        cv.put("last_read_at", System.currentTimeMillis());
        cv.put("reading_time_millis", 0);

        Cursor c = db.query(BibleDatabaseHelper.TABLE_READING_PROGRESS, new String[]{"_id"},
                "book_id=? AND chapter=?", new String[]{String.valueOf(bookId), String.valueOf(chapter)},
                null, null, null);

        if (c != null && c.moveToFirst()) {
            long id = c.getLong(0);
            c.close();
            db.update(BibleDatabaseHelper.TABLE_READING_PROGRESS, cv, "_id=?", new String[]{String.valueOf(id)});
        } else {
            if (c != null) c.close();
            db.insert(BibleDatabaseHelper.TABLE_READING_PROGRESS, null, cv);
        }
    }

    public ReadingProgress getLastReading() {
        Cursor c = db.query(BibleDatabaseHelper.TABLE_READING_PROGRESS, null,
                null, null, null, null, "last_read_at DESC", "1");
        if (c != null && c.moveToFirst()) {
            ReadingProgress rp = cursorToProgress(c);
            c.close();
            return rp;
        }
        return null;
    }

    public ReadingProgress getProgress(long bookId, int chapter) {
        Cursor c = db.query(BibleDatabaseHelper.TABLE_READING_PROGRESS, null,
                "book_id=? AND chapter=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter)},
                null, null, null);
        if (c != null && c.moveToFirst()) {
            ReadingProgress rp = cursorToProgress(c);
            c.close();
            return rp;
        }
        return null;
    }

    public void deleteAll() {
        db.delete(BibleDatabaseHelper.TABLE_READING_PROGRESS, null, null);
    }

    private ReadingProgress cursorToProgress(Cursor c) {
        ReadingProgress rp = new ReadingProgress();
        rp.setId(c.getLong(c.getColumnIndexOrThrow("_id")));
        rp.setBookId(c.getLong(c.getColumnIndexOrThrow("book_id")));
        rp.setChapter(c.getInt(c.getColumnIndexOrThrow("chapter")));
        rp.setVerse(c.getInt(c.getColumnIndexOrThrow("verse")));
        rp.setLastReadDate(new Date(c.getLong(c.getColumnIndexOrThrow("last_read_at"))));
        rp.setReadingTimeMillis(c.getLong(c.getColumnIndexOrThrow("reading_time_millis")));
        return rp;
    }
}
