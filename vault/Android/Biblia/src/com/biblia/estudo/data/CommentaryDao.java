package com.biblia.estudo.data;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import com.biblia.estudo.model.Commentary;

import java.util.ArrayList;
import java.util.List;

public class CommentaryDao {

    private SQLiteDatabase db;

    public CommentaryDao(SQLiteDatabase db) {
        this.db = db;
    }

    public long insert(Commentary commentary) {
        ContentValues cv = new ContentValues();
        cv.put("author_id", commentary.getAuthor());
        cv.put("book_id", commentary.getBookId());
        cv.put("chapter", commentary.getChapter());
        cv.put("verse_start", commentary.getVerseStart());
        cv.put("verse_end", commentary.getVerseEnd());
        cv.put("title", commentary.getTitle());
        cv.put("content", commentary.getContent());
        cv.put("category", commentary.getCategory());
        return db.insert(CommentaryDatabaseHelper.TABLE_COMMENTARIES, null, cv);
    }

    public List<Commentary> getByVerse(long bookId, int chapter, int verse) {
        List<Commentary> list = new ArrayList<>();
        Cursor c = db.rawQuery(
                "SELECT * FROM " + CommentaryDatabaseHelper.TABLE_COMMENTARIES +
                        " WHERE book_id=? AND chapter=? AND " +
                        "(verse_start=0 OR (verse_start<=? AND (verse_end=0 OR verse_end>=?))) " +
                        "ORDER BY verse_start ASC",
                new String[]{String.valueOf(bookId), String.valueOf(chapter),
                        String.valueOf(verse), String.valueOf(verse)});
        if (c != null) {
            while (c.moveToNext()) {
                list.add(cursorToCommentary(c));
            }
            c.close();
        }
        return list;
    }

    public List<Commentary> getByChapter(long bookId, int chapter) {
        List<Commentary> list = new ArrayList<>();
        Cursor c = db.query(CommentaryDatabaseHelper.TABLE_COMMENTARIES, null,
                "book_id=? AND chapter=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter)},
                null, null, "verse_start ASC");
        if (c != null) {
            while (c.moveToNext()) {
                list.add(cursorToCommentary(c));
            }
            c.close();
        }
        return list;
    }

    public int getCount(long bookId, int chapter) {
        Cursor c = db.rawQuery(
                "SELECT COUNT(*) FROM " + CommentaryDatabaseHelper.TABLE_COMMENTARIES +
                        " WHERE book_id=? AND chapter=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter)});
        int count = 0;
        if (c != null && c.moveToFirst()) {
            count = c.getInt(0);
            c.close();
        }
        return count;
    }

    private Commentary cursorToCommentary(Cursor c) {
        Commentary commentary = new Commentary();
        commentary.setId(c.getLong(c.getColumnIndexOrThrow("_id")));
        commentary.setBookId(c.getLong(c.getColumnIndexOrThrow("book_id")));
        commentary.setChapter(c.getInt(c.getColumnIndexOrThrow("chapter")));
        commentary.setVerseStart(c.getInt(c.getColumnIndexOrThrow("verse_start")));
        commentary.setVerseEnd(c.getInt(c.getColumnIndexOrThrow("verse_end")));
        commentary.setTitle(c.getString(c.getColumnIndexOrThrow("title")));
        commentary.setContent(c.getString(c.getColumnIndexOrThrow("content")));
        commentary.setCategory(c.getString(c.getColumnIndexOrThrow("category")));
        return commentary;
    }
}
